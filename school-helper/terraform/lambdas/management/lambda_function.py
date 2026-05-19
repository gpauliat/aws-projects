"""PDF and Quiz Management Lambda Handler.

Handles listing user PDFs, deleting PDFs with cascade deletion of associated
quizzes and quiz attempts, and deleting individual quizzes with cascade
deletion of associated quiz attempts.
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
s3 = boto3.client("s3")

PDFS_TABLE_NAME = os.environ["DYNAMODB_PDFS_TABLE_NAME"]
QUIZZES_TABLE_NAME = os.environ["DYNAMODB_QUIZZES_TABLE_NAME"]
QUIZ_ATTEMPTS_TABLE_NAME = os.environ["DYNAMODB_QUIZ_ATTEMPTS_TABLE_NAME"]
S3_BUCKET_NAME = os.environ["S3_BUCKET_NAME"]

pdfs_table = dynamodb.Table(PDFS_TABLE_NAME)
quizzes_table = dynamodb.Table(QUIZZES_TABLE_NAME)
quiz_attempts_table = dynamodb.Table(QUIZ_ATTEMPTS_TABLE_NAME)

PDFS_USER_INDEX = "userId-uploadedAt-index"
QUIZZES_PDF_INDEX = "pdfId-createdAt-index"
ATTEMPTS_QUIZ_INDEX = "quizId-completedAt-index"


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
        # GET /pdfs — list user's PDFs
        if http_method == "GET" and resource == "/pdfs":
            return _handle_list_pdfs(user_id)

        # DELETE /pdfs/{pdfId} — cascade delete PDF, quizzes, and attempts
        if http_method == "DELETE" and resource == "/pdfs/{pdfId}":
            pdf_id = path_params.get("pdfId")
            if not pdf_id:
                return _error(400, "Missing required parameter: pdfId.")
            return _handle_delete_pdf(user_id, pdf_id)

        # DELETE /quizzes/{quizId} — cascade delete quiz and attempts
        if http_method == "DELETE" and resource == "/quizzes/{quizId}":
            quiz_id = path_params.get("quizId")
            if not quiz_id:
                return _error(400, "Missing required parameter: quizId.")
            return _handle_delete_quiz(user_id, quiz_id)

        return _error(404, "The requested resource was not found.")

    except ClientError as e:
        logger.error("DynamoDB error: %s", str(e))
        return _error(500, "An internal error occurred. Please try again later.")
    except Exception as e:
        logger.error("Unexpected error: %s", str(e))
        return _error(500, "An internal error occurred. Please try again later.")


def _handle_list_pdfs(user_id):
    """List all PDFs belonging to the user, sorted by upload date (newest first)."""
    response = pdfs_table.query(
        IndexName=PDFS_USER_INDEX,
        KeyConditionExpression="userId = :uid",
        ExpressionAttributeValues={":uid": user_id},
        ScanIndexForward=False,  # newest first
    )

    pdfs = []
    for item in response.get("Items", []):
        pdfs.append({
            "pdfId": item.get("pdfId"),
            "fileName": item.get("fileName"),
            "uploadedAt": item.get("uploadedAt"),
            "extractionStatus": item.get("extractionStatus"),
            "quizCount": item.get("quizCount", 0),
        })

    return {
        "statusCode": 200,
        "headers": _cors_headers(),
        "body": json.dumps({"pdfs": pdfs}, cls=DecimalEncoder),
    }


def _handle_delete_pdf(user_id, pdf_id):
    """Delete a PDF and cascade delete all associated quizzes and quiz attempts."""
    # Fetch the PDF record to verify ownership and get the S3 key
    response = pdfs_table.get_item(Key={"pdfId": pdf_id})
    pdf = response.get("Item")

    if not pdf:
        return _error(404, "The requested resource was not found.")

    if pdf.get("userId") != user_id:
        return _error(403, "You don't have permission to access this resource.")

    s3_key = pdf.get("s3Key", "")
    errors = []

    # Step 1: Query all quizzes for this PDF
    quizzes = _query_all_quizzes_for_pdf(pdf_id)
    quiz_ids = [q["quizId"] for q in quizzes]

    # Step 2: Delete all quiz attempts for each quiz
    for quiz_id in quiz_ids:
        try:
            _delete_attempts_for_quiz(quiz_id)
        except Exception as e:
            logger.error(
                "Failed to delete attempts for quizId=%s: %s", quiz_id, str(e)
            )
            errors.append(f"Failed to delete some attempts for quiz {quiz_id}.")

    # Step 3: Batch delete all quizzes
    if quizzes:
        try:
            _batch_delete_items(quizzes_table, [{"quizId": q["quizId"]} for q in quizzes])
        except Exception as e:
            logger.error("Failed to delete quizzes for pdfId=%s: %s", pdf_id, str(e))
            errors.append("Failed to delete some quizzes.")

    # Step 4: Delete the PDF record from DynamoDB
    try:
        pdfs_table.delete_item(Key={"pdfId": pdf_id})
    except Exception as e:
        logger.error("Failed to delete PDF record pdfId=%s: %s", pdf_id, str(e))
        errors.append("Failed to delete the PDF record.")

    # Step 5: Delete the PDF file from S3
    if s3_key:
        try:
            s3.delete_object(Bucket=S3_BUCKET_NAME, Key=s3_key)
        except Exception as e:
            logger.error(
                "Failed to delete S3 object s3Key=%s: %s", s3_key, str(e)
            )
            errors.append("Failed to delete the PDF file from storage.")

    if errors:
        logger.warning(
            "Partial deletion failure for pdfId=%s: %s", pdf_id, "; ".join(errors)
        )
        return {
            "statusCode": 207,
            "headers": _cors_headers(),
            "body": json.dumps({
                "message": "PDF deleted with some errors. Please try again or contact support.",
                "errors": errors,
            }),
        }

    logger.info(
        "PDF deleted: pdfId=%s, quizzes=%d, s3Key=%s",
        pdf_id,
        len(quiz_ids),
        s3_key,
    )

    return {
        "statusCode": 200,
        "headers": _cors_headers(),
        "body": json.dumps({
            "message": "PDF and all associated data deleted successfully.",
            "pdfId": pdf_id,
            "deletedQuizzes": len(quiz_ids),
        }),
    }


def _handle_delete_quiz(user_id, quiz_id):
    """Delete a quiz and cascade delete all associated quiz attempts."""
    # Fetch the quiz record to verify ownership
    response = quizzes_table.get_item(Key={"quizId": quiz_id})
    quiz = response.get("Item")

    if not quiz:
        return _error(404, "The requested resource was not found.")

    if quiz.get("userId") != user_id:
        return _error(403, "You don't have permission to access this resource.")

    pdf_id = quiz.get("pdfId", "")
    errors = []

    # Step 1: Delete all quiz attempts for this quiz
    try:
        _delete_attempts_for_quiz(quiz_id)
    except Exception as e:
        logger.error("Failed to delete attempts for quizId=%s: %s", quiz_id, str(e))
        errors.append("Failed to delete some quiz attempts.")

    # Step 2: Delete the quiz record
    try:
        quizzes_table.delete_item(Key={"quizId": quiz_id})
    except Exception as e:
        logger.error("Failed to delete quiz record quizId=%s: %s", quiz_id, str(e))
        errors.append("Failed to delete the quiz record.")

    # Step 3: Decrement quizCount on the parent PDF
    if pdf_id:
        try:
            pdfs_table.update_item(
                Key={"pdfId": pdf_id},
                UpdateExpression="SET quizCount = if_not_exists(quizCount, :one) - :one",
                ExpressionAttributeValues={":one": 1},
            )
        except Exception as e:
            logger.error(
                "Failed to decrement quizCount for pdfId=%s: %s", pdf_id, str(e)
            )
            errors.append("Failed to update quiz count on the PDF.")

    if errors:
        logger.warning(
            "Partial deletion failure for quizId=%s: %s", quiz_id, "; ".join(errors)
        )
        return {
            "statusCode": 207,
            "headers": _cors_headers(),
            "body": json.dumps({
                "message": "Quiz deleted with some errors. Please try again or contact support.",
                "errors": errors,
            }),
        }

    logger.info("Quiz deleted: quizId=%s, pdfId=%s", quiz_id, pdf_id)

    return {
        "statusCode": 200,
        "headers": _cors_headers(),
        "body": json.dumps({
            "message": "Quiz and all associated data deleted successfully.",
            "quizId": quiz_id,
        }),
    }


def _query_all_quizzes_for_pdf(pdf_id):
    """Query all quizzes associated with a PDF using the GSI."""
    quizzes = []
    response = quizzes_table.query(
        IndexName=QUIZZES_PDF_INDEX,
        KeyConditionExpression="pdfId = :pid",
        ExpressionAttributeValues={":pid": pdf_id},
        ProjectionExpression="quizId",
    )
    quizzes.extend(response.get("Items", []))

    # Handle pagination
    while "LastEvaluatedKey" in response:
        response = quizzes_table.query(
            IndexName=QUIZZES_PDF_INDEX,
            KeyConditionExpression="pdfId = :pid",
            ExpressionAttributeValues={":pid": pdf_id},
            ProjectionExpression="quizId",
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
        quizzes.extend(response.get("Items", []))

    return quizzes


def _query_all_attempts_for_quiz(quiz_id):
    """Query all quiz attempts associated with a quiz using the GSI."""
    attempts = []
    response = quiz_attempts_table.query(
        IndexName=ATTEMPTS_QUIZ_INDEX,
        KeyConditionExpression="quizId = :qid",
        ExpressionAttributeValues={":qid": quiz_id},
        ProjectionExpression="attemptId",
    )
    attempts.extend(response.get("Items", []))

    # Handle pagination
    while "LastEvaluatedKey" in response:
        response = quiz_attempts_table.query(
            IndexName=ATTEMPTS_QUIZ_INDEX,
            KeyConditionExpression="quizId = :qid",
            ExpressionAttributeValues={":qid": quiz_id},
            ProjectionExpression="attemptId",
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
        attempts.extend(response.get("Items", []))

    return attempts


def _delete_attempts_for_quiz(quiz_id):
    """Delete all quiz attempts for a given quiz using batch writes."""
    attempts = _query_all_attempts_for_quiz(quiz_id)
    if attempts:
        _batch_delete_items(
            quiz_attempts_table,
            [{"attemptId": a["attemptId"]} for a in attempts],
        )


def _batch_delete_items(table, keys):
    """Delete multiple items from a DynamoDB table using batch_writer.

    The batch_writer context manager automatically handles batching
    into groups of 25 items per request.
    """
    with table.batch_writer() as batch:
        for key in keys:
            batch.delete_item(Key=key)


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
        "Access-Control-Allow-Methods": "OPTIONS,GET,DELETE",
    }
