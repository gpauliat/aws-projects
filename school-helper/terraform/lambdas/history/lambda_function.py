"""History and Progress Lambda Handler.

Handles quiz history listing, detailed attempt retrieval, and per-PDF
progress tracking (average score) in DynamoDB.
"""

import json
import logging
import os
from decimal import Decimal
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")

QUIZ_ATTEMPTS_TABLE_NAME = os.environ["DYNAMODB_QUIZ_ATTEMPTS_TABLE_NAME"]
QUIZZES_TABLE_NAME = os.environ["DYNAMODB_QUIZZES_TABLE_NAME"]
PDFS_TABLE_NAME = os.environ["DYNAMODB_PDFS_TABLE_NAME"]

quiz_attempts_table = dynamodb.Table(QUIZ_ATTEMPTS_TABLE_NAME)
quizzes_table = dynamodb.Table(QUIZZES_TABLE_NAME)
pdfs_table = dynamodb.Table(PDFS_TABLE_NAME)

ATTEMPTS_USER_INDEX = "userId-completedAt-index"
ATTEMPTS_PDF_INDEX = "pdfId-completedAt-index"


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that converts Decimal values to int or float."""

    def default(self, o):
        if isinstance(o, Decimal):
            if o % 1 == 0:
                return int(o)
            return float(o)
        return super().default(o)


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
        # GET /history — list all quiz attempts for user
        if http_method == "GET" and resource == "/history":
            return _handle_list_history(user_id)

        # GET /history/{attemptId} — detailed results for a specific attempt
        if http_method == "GET" and resource == "/history/{attemptId}":
            attempt_id = path_params.get("attemptId")
            if not attempt_id:
                return _error(400, "Missing required parameter: attemptId.")
            return _handle_get_attempt(user_id, attempt_id)

        # GET /progress/pdf/{pdfId} — average score for a PDF
        if http_method == "GET" and resource == "/progress/pdf/{pdfId}":
            pdf_id = path_params.get("pdfId")
            if not pdf_id:
                return _error(400, "Missing required parameter: pdfId.")
            return _handle_pdf_progress(user_id, pdf_id)

        return _error(404, "The requested resource was not found.")

    except ClientError as e:
        logger.error("DynamoDB error: %s", str(e))
        return _error(500, "An internal error occurred. Please try again later.")
    except Exception as e:
        logger.error("Unexpected error: %s", str(e))
        return _error(500, "An internal error occurred. Please try again later.")


def _handle_list_history(user_id):
    """List all quiz attempts for the user, sorted by completion date (newest first)."""
    response = quiz_attempts_table.query(
        IndexName=ATTEMPTS_USER_INDEX,
        KeyConditionExpression="userId = :uid",
        ExpressionAttributeValues={":uid": user_id},
        ScanIndexForward=False,  # newest first
    )

    attempts = response.get("Items", [])

    # Collect unique pdfIds to look up file names
    pdf_ids = list({a.get("pdfId") for a in attempts if a.get("pdfId")})
    pdf_names = _get_pdf_names(pdf_ids)

    history = []
    for item in attempts:
        pdf_id = item.get("pdfId", "")
        history.append({
            "attemptId": item.get("attemptId"),
            "quizId": item.get("quizId"),
            "pdfId": pdf_id,
            "pdfFileName": pdf_names.get(pdf_id, ""),
            "completedAt": item.get("completedAt"),
            "scorePercent": item.get("scorePercent"),
            "totalQuestions": item.get("totalQuestions"),
            "correctCount": item.get("correctCount"),
        })

    return {
        "statusCode": 200,
        "headers": _cors_headers(),
        "body": json.dumps({"history": history}, cls=DecimalEncoder),
    }


def _handle_get_attempt(user_id, attempt_id):
    """Get detailed results for a specific quiz attempt, including quiz questions."""
    response = quiz_attempts_table.get_item(Key={"attemptId": attempt_id})
    attempt = response.get("Item")

    if not attempt:
        return _error(404, "The requested resource was not found.")

    # Verify the attempt belongs to the requesting user
    if attempt.get("userId") != user_id:
        return _error(403, "You don't have permission to access this resource.")

    # Fetch the quiz to include question details (prompts, options, correct answers)
    quiz_id = attempt.get("quizId")
    quiz = None
    if quiz_id:
        quiz_response = quizzes_table.get_item(Key={"quizId": quiz_id})
        quiz = quiz_response.get("Item")

    # Build a question lookup map
    question_map = {}
    if quiz:
        for q in quiz.get("questions", []):
            question_map[q["questionId"]] = q

    # Merge attempt answers with question details
    detailed_results = []
    for answer in attempt.get("answers", []):
        question_id = answer.get("questionId")
        question = question_map.get(question_id, {})

        detailed_results.append({
            "questionId": question_id,
            "prompt": question.get("prompt", ""),
            "options": question.get("options", []),
            "selectedOptionIndex": answer.get("selectedOptionIndex"),
            "correctOptionIndex": question.get("correctOptionIndex"),
            "isCorrect": answer.get("isCorrect"),
            "difficulty": question.get("difficulty", ""),
        })

    # Look up PDF file name
    pdf_id = attempt.get("pdfId", "")
    pdf_names = _get_pdf_names([pdf_id]) if pdf_id else {}

    result = {
        "attemptId": attempt.get("attemptId"),
        "quizId": quiz_id,
        "pdfId": pdf_id,
        "pdfFileName": pdf_names.get(pdf_id, ""),
        "quizTitle": quiz.get("title", "") if quiz else "",
        "completedAt": attempt.get("completedAt"),
        "scorePercent": attempt.get("scorePercent"),
        "totalQuestions": attempt.get("totalQuestions"),
        "correctCount": attempt.get("correctCount"),
        "results": detailed_results,
    }

    return {
        "statusCode": 200,
        "headers": _cors_headers(),
        "body": json.dumps(result, cls=DecimalEncoder),
    }


def _handle_pdf_progress(user_id, pdf_id):
    """Calculate average score across all attempts for a specific PDF."""
    # Query all attempts for this PDF
    response = quiz_attempts_table.query(
        IndexName=ATTEMPTS_PDF_INDEX,
        KeyConditionExpression="pdfId = :pid",
        ExpressionAttributeValues={":pid": pdf_id},
        ScanIndexForward=False,
    )

    attempts = response.get("Items", [])

    # Filter to only the requesting user's attempts
    user_attempts = [a for a in attempts if a.get("userId") == user_id]

    if not user_attempts:
        return _error(404, "The requested resource was not found.")

    # Calculate arithmetic mean of scorePercent values, rounded to nearest integer
    scores = [int(a.get("scorePercent", 0)) for a in user_attempts]
    average_score = round(sum(scores) / len(scores))

    # Look up PDF file name
    pdf_names = _get_pdf_names([pdf_id])

    return {
        "statusCode": 200,
        "headers": _cors_headers(),
        "body": json.dumps({
            "pdfId": pdf_id,
            "pdfFileName": pdf_names.get(pdf_id, ""),
            "averageScore": average_score,
            "totalAttempts": len(user_attempts),
        }, cls=DecimalEncoder),
    }


def _get_pdf_names(pdf_ids):
    """Batch-fetch PDF file names by their IDs. Returns a dict of pdfId -> fileName."""
    if not pdf_ids:
        return {}

    pdf_names = {}
    for pdf_id in pdf_ids:
        try:
            response = pdfs_table.get_item(
                Key={"pdfId": pdf_id},
                ProjectionExpression="pdfId, fileName",
            )
            item = response.get("Item")
            if item:
                pdf_names[pdf_id] = item.get("fileName", "")
        except ClientError:
            logger.warning("Failed to fetch PDF name for pdfId=%s", pdf_id)
            pdf_names[pdf_id] = ""

    return pdf_names


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
        "Access-Control-Allow-Methods": "OPTIONS,GET",
    }
