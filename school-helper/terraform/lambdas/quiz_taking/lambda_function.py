"""Quiz Taking Lambda Handler.

Handles quiz listing, quiz retrieval for taking (excluding correct answers),
quiz submission with scoring, and quiz attempt recording in DynamoDB.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")

QUIZZES_TABLE_NAME = os.environ["DYNAMODB_QUIZZES_TABLE_NAME"]
QUIZ_ATTEMPTS_TABLE_NAME = os.environ["DYNAMODB_QUIZ_ATTEMPTS_TABLE_NAME"]

quizzes_table = dynamodb.Table(QUIZZES_TABLE_NAME)
quiz_attempts_table = dynamodb.Table(QUIZ_ATTEMPTS_TABLE_NAME)

QUIZZES_USER_INDEX = "userId-createdAt-index"


def lambda_handler(event, context):
    """Route requests to the appropriate handler based on HTTP method and path."""
    # Extract userId from Cognito JWT claims
    try:
        user_id = event["requestContext"]["authorizer"]["claims"]["sub"]
    except (KeyError, TypeError):
        return _error(401, "Unauthorized.")

    http_method = event.get("httpMethod", "")
    resource = event.get("resource", "")
    path_params = event.get("pathParameters") or {}

    try:
        # GET /quizzes — list user's quizzes
        if http_method == "GET" and resource == "/quizzes":
            return _handle_list_quizzes(user_id)

        # GET /quizzes/{quizId} — get quiz for taking
        if http_method == "GET" and resource == "/quizzes/{quizId}":
            quiz_id = path_params.get("quizId")
            if not quiz_id:
                return _error(400, "Missing required parameter: quizId.")
            return _handle_get_quiz(user_id, quiz_id)

        # POST /quizzes/{quizId}/submit — submit answers and score
        if http_method == "POST" and resource == "/quizzes/{quizId}/submit":
            quiz_id = path_params.get("quizId")
            if not quiz_id:
                return _error(400, "Missing required parameter: quizId.")
            return _handle_submit_quiz(user_id, quiz_id, event)

        return _error(404, "The requested resource was not found.")

    except ClientError as e:
        logger.error("DynamoDB error: %s", str(e))
        return _error(500, "An internal error occurred. Please try again later.")
    except Exception as e:
        logger.error("Unexpected error: %s", str(e))
        return _error(500, "An internal error occurred. Please try again later.")


def _handle_list_quizzes(user_id):
    """List all quizzes belonging to the user, sorted by creation date."""
    response = quizzes_table.query(
        IndexName=QUIZZES_USER_INDEX,
        KeyConditionExpression="userId = :uid",
        ExpressionAttributeValues={":uid": user_id},
        ScanIndexForward=False,  # newest first
    )

    quizzes = []
    for item in response.get("Items", []):
        quizzes.append({
            "quizId": item.get("quizId"),
            "pdfId": item.get("pdfId"),
            "title": item.get("title"),
            "createdAt": item.get("createdAt"),
            "questionCount": len(item.get("questions", [])),
        })

    return {
        "statusCode": 200,
        "headers": _cors_headers(),
        "body": json.dumps({"quizzes": quizzes}),
    }


def _handle_get_quiz(user_id, quiz_id):
    """Get a quiz for taking — returns questions WITHOUT correctOptionIndex."""
    response = quizzes_table.get_item(Key={"quizId": quiz_id})
    quiz = response.get("Item")

    if not quiz:
        return _error(404, "The requested resource was not found.")

    # Verify the quiz belongs to the requesting user
    if quiz.get("userId") != user_id:
        return _error(403, "You don't have permission to access this resource.")

    # Build questions list without correctOptionIndex
    questions = []
    for q in quiz.get("questions", []):
        questions.append({
            "questionId": q.get("questionId"),
            "prompt": q.get("prompt"),
            "options": q.get("options"),
            "difficulty": q.get("difficulty"),
        })

    return {
        "statusCode": 200,
        "headers": _cors_headers(),
        "body": json.dumps({
            "quizId": quiz.get("quizId"),
            "pdfId": quiz.get("pdfId"),
            "title": quiz.get("title"),
            "createdAt": quiz.get("createdAt"),
            "questions": questions,
        }),
    }


def _handle_submit_quiz(user_id, quiz_id, event):
    """Submit quiz answers, calculate score, and create a QuizAttempt record."""
    # Parse request body
    try:
        body = json.loads(event.get("body") or "{}")
    except (json.JSONDecodeError, TypeError):
        return _error(400, "Invalid request body.")

    answers = body.get("answers")
    if not isinstance(answers, list) or len(answers) == 0:
        return _error(400, "Missing or empty answers list.")

    # Fetch the quiz
    response = quizzes_table.get_item(Key={"quizId": quiz_id})
    quiz = response.get("Item")

    if not quiz:
        return _error(404, "The requested resource was not found.")

    # Verify the quiz belongs to the requesting user
    if quiz.get("userId") != user_id:
        return _error(403, "You don't have permission to access this resource.")

    questions = quiz.get("questions", [])
    if not questions:
        return _error(400, "This quiz has no questions.")

    # Build a lookup of questionId -> question for scoring
    question_map = {}
    for q in questions:
        question_map[q["questionId"]] = q

    # Score the answers
    total_questions = len(questions)
    correct_count = 0
    answer_details = []
    results = []

    for submitted in answers:
        question_id = submitted.get("questionId")
        selected_index = submitted.get("selectedOptionIndex")

        if question_id is None or selected_index is None:
            return _error(400, "Each answer must include questionId and selectedOptionIndex.")

        # Validate selectedOptionIndex
        try:
            selected_index = int(selected_index)
        except (ValueError, TypeError):
            return _error(400, "selectedOptionIndex must be an integer.")

        if selected_index < 0 or selected_index > 3:
            return _error(400, "selectedOptionIndex must be between 0 and 3.")

        question = question_map.get(question_id)
        if not question:
            return _error(400, f"Invalid questionId: {question_id}.")

        correct_index = int(question["correctOptionIndex"])
        is_correct = selected_index == correct_index

        if is_correct:
            correct_count += 1

        answer_details.append({
            "questionId": question_id,
            "selectedOptionIndex": selected_index,
            "isCorrect": is_correct,
        })

        # Build result entry for the response
        result_entry = {
            "questionId": question_id,
            "prompt": question.get("prompt"),
            "options": question.get("options"),
            "selectedOptionIndex": selected_index,
            "isCorrect": is_correct,
        }

        # Include correct answer for incorrectly answered questions
        if not is_correct:
            result_entry["correctOptionIndex"] = correct_index

        results.append(result_entry)

    # Calculate score: (correct_count / total_questions) * 100, rounded to nearest integer
    score_percent = round((correct_count / total_questions) * 100)

    # Create QuizAttempt record
    attempt_id = str(uuid.uuid4())
    completed_at = datetime.now(timezone.utc).isoformat()

    attempt_item = {
        "attemptId": attempt_id,
        "quizId": quiz_id,
        "userId": user_id,
        "pdfId": quiz.get("pdfId", ""),
        "completedAt": completed_at,
        "scorePercent": score_percent,
        "totalQuestions": total_questions,
        "correctCount": correct_count,
        "answers": answer_details,
    }

    quiz_attempts_table.put_item(Item=attempt_item)

    logger.info(
        "Quiz submitted: attemptId=%s, quizId=%s, score=%d%% (%d/%d)",
        attempt_id,
        quiz_id,
        score_percent,
        correct_count,
        total_questions,
    )

    return {
        "statusCode": 200,
        "headers": _cors_headers(),
        "body": json.dumps({
            "attemptId": attempt_id,
            "quizId": quiz_id,
            "scorePercent": score_percent,
            "totalQuestions": total_questions,
            "correctCount": correct_count,
            "completedAt": completed_at,
            "results": results,
        }),
    }


def _error(status_code, message):
    """Return a formatted error response."""
    return {
        "statusCode": status_code,
        "headers": _cors_headers(),
        "body": json.dumps({"error": message}),
    }


def _cors_headers():
    """Return standard CORS headers."""
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "OPTIONS,GET,POST",
    }
