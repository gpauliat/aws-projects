"""PDF Upload Lambda Handler.

Generates a presigned S3 PUT URL for PDF upload and creates a PDF record
in DynamoDB with extractionStatus = "pending".
"""

import json
import os
import uuid
from datetime import datetime, timezone

import boto3
from botocore.config import Config

_region = os.environ.get("AWS_REGION", "eu-west-3")

s3_client = boto3.client(
    "s3",
    region_name=_region,
    config=Config(
        signature_version="s3v4",
        s3={"addressing_style": "virtual"},
    ),
)
dynamodb = boto3.resource("dynamodb")

BUCKET_NAME = os.environ["S3_BUCKET_NAME"]
TABLE_NAME = os.environ["DYNAMODB_TABLE_NAME"]
MAX_FILE_SIZE = int(os.environ.get("MAX_FILE_SIZE", 52428800))  # 50 MB

table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    """Handle PDF upload URL generation requests."""
    try:
        body = json.loads(event.get("body") or "{}")
    except (json.JSONDecodeError, TypeError):
        return _error(400, "Invalid request body.")

    file_name = body.get("fileName", "")
    file_size = body.get("fileSize", 0)
    content_type = body.get("contentType", "")

    # Validate file type
    if content_type != "application/pdf":
        return _error(400, "Only PDF files are supported. Please select a PDF file.")

    # Validate file size
    try:
        file_size = int(file_size)
    except (ValueError, TypeError):
        return _error(400, "Invalid file size.")

    if file_size <= 0:
        return _error(400, "Invalid file size.")

    if file_size > MAX_FILE_SIZE:
        return _error(
            400,
            "File size exceeds the 50 MB limit. Please upload a smaller file.",
        )

    # Extract userId from Cognito JWT claims
    try:
        user_id = event["requestContext"]["authorizer"]["claims"]["sub"]
    except (KeyError, TypeError):
        return _error(401, "Unauthorized.")

    pdf_id = str(uuid.uuid4())
    s3_key = f"pdfs/{pdf_id}.pdf"
    uploaded_at = datetime.now(timezone.utc).isoformat()

    # Generate presigned PUT URL
    presigned_url = s3_client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": s3_key,
            "ContentType": "application/pdf",
        },
        ExpiresIn=300,
    )

    # Create PDF record in DynamoDB
    table.put_item(
        Item={
            "pdfId": pdf_id,
            "userId": user_id,
            "fileName": file_name,
            "s3Key": s3_key,
            "fileSizeBytes": file_size,
            "uploadedAt": uploaded_at,
            "extractionStatus": "pending",
            "quizCount": 0,
        }
    )

    return {
        "statusCode": 200,
        "headers": _cors_headers(),
        "body": json.dumps({"pdfId": pdf_id, "uploadUrl": presigned_url}),
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
        "Access-Control-Allow-Methods": "OPTIONS,POST",
    }
