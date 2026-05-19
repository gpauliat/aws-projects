"""Knowledge Base Sync Lambda Handler.

Triggered by S3 event when a PDF is uploaded to the pdfs/ prefix. Starts
a Bedrock Knowledge Base ingestion job, polls until completion, and
updates the PDF record status in DynamoDB.
"""

import logging
import os
import time

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock_agent_client = boto3.client("bedrock-agent")
dynamodb = boto3.resource("dynamodb")

TABLE_NAME = os.environ["DYNAMODB_TABLE_NAME"]
KNOWLEDGE_BASE_ID = os.environ["KNOWLEDGE_BASE_ID"]
DATA_SOURCE_ID = os.environ["DATA_SOURCE_ID"]

table = dynamodb.Table(TABLE_NAME)

MAX_POLL_ATTEMPTS = 60
BASE_DELAY = 2  # seconds
MAX_DELAY = 30  # seconds


def lambda_handler(event, context):
    """Handle S3 event and sync uploaded PDF to Bedrock Knowledge Base."""
    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        # Derive pdfId from the S3 key (e.g. "pdfs/<uuid>.pdf" -> "<uuid>")
        pdf_id = key.split("/")[-1].replace(".pdf", "")

        logger.info("Processing PDF: bucket=%s, key=%s, pdfId=%s", bucket, key, pdf_id)

        # Mark status as syncing
        _update_status(pdf_id, "syncing")

        try:
            _start_and_poll_ingestion(pdf_id)

            # Ingestion succeeded
            _update_status(pdf_id, "ready")
            logger.info("Knowledge Base sync completed for pdfId=%s", pdf_id)

        except Exception as e:
            logger.error("Knowledge Base sync failed for pdfId=%s: %s", pdf_id, str(e))
            _update_status(
                pdf_id,
                "failed",
                error_message="Knowledge Base sync failed. Please try uploading the document again.",
            )


def _start_and_poll_ingestion(pdf_id):
    """Start a KB ingestion job and poll until it completes or fails."""
    # Start the ingestion job
    response = bedrock_agent_client.start_ingestion_job(
        knowledgeBaseId=KNOWLEDGE_BASE_ID,
        dataSourceId=DATA_SOURCE_ID,
    )

    ingestion_job = response.get("ingestionJob", {})
    ingestion_job_id = ingestion_job["ingestionJobId"]

    logger.info(
        "Started ingestion job: jobId=%s, pdfId=%s",
        ingestion_job_id,
        pdf_id,
    )

    # Poll with exponential backoff
    for attempt in range(MAX_POLL_ATTEMPTS):
        delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
        time.sleep(delay)

        try:
            status_response = bedrock_agent_client.get_ingestion_job(
                knowledgeBaseId=KNOWLEDGE_BASE_ID,
                dataSourceId=DATA_SOURCE_ID,
                ingestionJobId=ingestion_job_id,
            )
        except ClientError as e:
            logger.warning(
                "Poll attempt %d/%d failed for jobId=%s: %s",
                attempt + 1,
                MAX_POLL_ATTEMPTS,
                ingestion_job_id,
                str(e),
            )
            continue

        job = status_response.get("ingestionJob", {})
        status = job.get("status", "")

        logger.info(
            "Ingestion job status: jobId=%s, status=%s, attempt=%d/%d",
            ingestion_job_id,
            status,
            attempt + 1,
            MAX_POLL_ATTEMPTS,
        )

        if status == "COMPLETE":
            return

        if status == "FAILED":
            failure_reasons = job.get("failureReasons", [])
            reason = "; ".join(failure_reasons) if failure_reasons else "Unknown error"
            raise RuntimeError(
                f"Ingestion job failed: jobId={ingestion_job_id}, reason={reason}"
            )

    # Exceeded max poll attempts
    raise RuntimeError(
        f"Ingestion job timed out after {MAX_POLL_ATTEMPTS} poll attempts: "
        f"jobId={ingestion_job_id}"
    )


def _update_status(pdf_id, status, error_message=None):
    """Update the extraction status of a PDF record in DynamoDB."""
    update_expr = "SET extractionStatus = :status"
    expr_values = {":status": status}

    if error_message:
        update_expr += ", extractionError = :err"
        expr_values[":err"] = error_message

    try:
        table.update_item(
            Key={"pdfId": pdf_id},
            UpdateExpression=update_expr,
            ExpressionAttributeValues=expr_values,
        )
    except Exception as e:
        logger.error("Failed to update status for pdfId=%s: %s", pdf_id, str(e))
