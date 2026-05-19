"""Quiz Generation Lambda Handler.

Receives a pdfId, verifies the PDF has been synced to the Knowledge Base,
retrieves relevant content via the Bedrock Knowledge Base retrieve API,
calls Amazon Bedrock to generate multiple-choice quiz questions,
validates the response, and stores the quiz in DynamoDB.
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
bedrock_runtime = boto3.client("bedrock-runtime")
bedrock_agent_runtime = boto3.client("bedrock-agent-runtime")

PDFS_TABLE_NAME = os.environ["DYNAMODB_PDFS_TABLE_NAME"]
QUIZZES_TABLE_NAME = os.environ["DYNAMODB_QUIZZES_TABLE_NAME"]
BEDROCK_MODEL_ID = os.environ["BEDROCK_MODEL_ID"]
KNOWLEDGE_BASE_ID = os.environ["KNOWLEDGE_BASE_ID"]
S3_BUCKET_NAME = os.environ["S3_BUCKET_NAME"]

pdfs_table = dynamodb.Table(PDFS_TABLE_NAME)
quizzes_table = dynamodb.Table(QUIZZES_TABLE_NAME)

QUIZZES_PDF_INDEX = "pdfId-createdAt-index"
MIN_QUESTIONS = 10
MAX_BEDROCK_RETRIES = 2  # initial attempt + 1 retry


def lambda_handler(event, context):
    """Handle quiz generation requests."""
    try:
        return _handle_request(event, context)
    except Exception as e:
        logger.error("Unhandled exception in quiz generation: %s", str(e), exc_info=True)
        return _error(500, "An internal error occurred. Please try again later.")


def _handle_request(event, context):
    """Internal handler for quiz generation requests."""
    # Extract userId from Cognito JWT claims
    try:
        user_id = event["requestContext"]["authorizer"]["claims"]["sub"]
    except (KeyError, TypeError):
        return _error(401, "Unauthorized.")

    # Parse request body
    try:
        body = json.loads(event.get("body") or "{}")
    except (json.JSONDecodeError, TypeError):
        return _error(400, "Invalid request body.")

    # Get pdfId from path parameters or body
    pdf_id = (event.get("pathParameters") or {}).get("pdfId") or body.get("pdfId")
    if not pdf_id:
        return _error(400, "Missing required parameter: pdfId.")

    # Fetch the PDF record
    try:
        pdf_response = pdfs_table.get_item(Key={"pdfId": pdf_id})
    except ClientError as e:
        logger.error("Failed to fetch PDF record: %s", str(e))
        return _error(500, "An internal error occurred. Please try again later.")

    pdf_item = pdf_response.get("Item")
    if not pdf_item:
        return _error(404, "The requested resource was not found.")

    # Verify the PDF belongs to the requesting user
    if pdf_item.get("userId") != user_id:
        return _error(403, "You don't have permission to access this resource.")

    # Verify Knowledge Base sync is complete
    extraction_status = pdf_item.get("extractionStatus")
    if extraction_status != "ready":
        return _error(
            400,
            "PDF text extraction is not complete. Current status: "
            f"{extraction_status}.",
        )

    # Retrieve content from Bedrock Knowledge Base
    s3_key = pdf_item.get("s3Key", "")
    logger.info(
        "Retrieving content from Knowledge Base for pdfId=%s, s3Key=%s",
        pdf_id,
        s3_key,
    )
    retrieved_content = _retrieve_from_knowledge_base(s3_key)
    if not retrieved_content:
        return _error(
            400,
            "No content could be retrieved from this PDF.",
        )

    # Fetch existing quiz question prompts for this PDF to avoid duplicates
    existing_prompts = _get_existing_prompts(pdf_id)

    # Generate quiz using Bedrock
    questions = None
    last_error = None

    for attempt in range(MAX_BEDROCK_RETRIES):
        try:
            raw_response = _call_bedrock(retrieved_content, existing_prompts)
            questions = _validate_quiz_response(raw_response)
            break
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            last_error = str(e)
            logger.warning(
                "Bedrock response validation failed (attempt %d/%d): %s",
                attempt + 1,
                MAX_BEDROCK_RETRIES,
                last_error,
            )
        except ClientError as e:
            last_error = str(e)
            logger.error("Bedrock API call failed: %s", last_error)
            break  # Don't retry on API errors
        except Exception as e:
            last_error = str(e)
            logger.error("Unexpected error during quiz generation: %s", last_error)
            break

    if questions is None:
        logger.error("Quiz generation failed after retries: %s", last_error)
        return _error(
            500,
            "Quiz generation failed. Please try again later.",
        )

    # Create quiz record
    quiz_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    title = _generate_title(pdf_item.get("fileName", "Document"))

    quiz_item = {
        "quizId": quiz_id,
        "pdfId": pdf_id,
        "userId": user_id,
        "title": title,
        "createdAt": created_at,
        "questions": questions,
    }

    try:
        # Store quiz in DynamoDB
        quizzes_table.put_item(Item=quiz_item)

        # Increment quizCount on the PDF record
        pdfs_table.update_item(
            Key={"pdfId": pdf_id},
            UpdateExpression="SET quizCount = if_not_exists(quizCount, :zero) + :inc",
            ExpressionAttributeValues={":zero": 0, ":inc": 1},
        )
    except ClientError as e:
        logger.error("Failed to store quiz: %s", str(e))
        return _error(500, "An internal error occurred. Please try again later.")

    logger.info(
        "Quiz generated: quizId=%s, pdfId=%s, questions=%d",
        quiz_id,
        pdf_id,
        len(questions),
    )

    return {
        "statusCode": 200,
        "headers": _cors_headers(),
        "body": json.dumps({
            "quizId": quiz_id,
            "title": title,
            "questionCount": len(questions),
        }),
    }


def _get_existing_prompts(pdf_id):
    """Fetch existing quiz question prompts for a PDF to avoid duplicates."""
    existing_prompts = []
    try:
        response = quizzes_table.query(
            IndexName=QUIZZES_PDF_INDEX,
            KeyConditionExpression="pdfId = :pid",
            ExpressionAttributeValues={":pid": pdf_id},
        )
        for quiz in response.get("Items", []):
            for question in quiz.get("questions", []):
                prompt = question.get("prompt", "")
                if prompt:
                    existing_prompts.append(prompt)
    except ClientError as e:
        logger.warning("Failed to fetch existing quizzes: %s", str(e))
        # Continue without existing prompts — duplicates are acceptable as fallback
    return existing_prompts


def _retrieve_from_knowledge_base(s3_key):
    """Retrieve content chunks from the Bedrock Knowledge Base for a specific PDF."""
    s3_uri = f"s3://{S3_BUCKET_NAME}/{s3_key}"

    # Try filtered retrieval first (by source URI)
    content = _do_retrieve(s3_uri, use_filter=True)
    if content:
        return content

    # Fallback: retrieve without filter (useful if metadata isn't indexed)
    logger.warning(
        "Filtered retrieval returned no results for %s, trying unfiltered.",
        s3_uri,
    )
    return _do_retrieve(s3_uri, use_filter=False)


def _do_retrieve(s3_uri, use_filter=True):
    """Execute a Knowledge Base retrieve call, optionally with a source URI filter."""
    try:
        retrieval_config = {"vectorSearchConfiguration": {"numberOfResults": 25}}

        if use_filter:
            retrieval_config["vectorSearchConfiguration"]["filter"] = {
                "equals": {
                    "key": "x-amz-bedrock-kb-source-uri",
                    "value": s3_uri,
                }
            }

        response = bedrock_agent_runtime.retrieve(
            knowledgeBaseId=KNOWLEDGE_BASE_ID,
            retrievalQuery={
                "text": "Retrieve all content from this document to generate quiz questions",
            },
            retrievalConfiguration=retrieval_config,
        )
    except ClientError as e:
        logger.error("Knowledge Base retrieve failed: %s", str(e))
        return ""

    results = response.get("retrievalResults", [])
    if not results:
        return ""

    # Assemble content chunks into a single text block
    chunks = []
    for result in results:
        text = result.get("content", {}).get("text", "")
        if text.strip():
            chunks.append(text.strip())

    return "\n\n".join(chunks)


def _call_bedrock(retrieved_content, existing_prompts):
    """Call Amazon Bedrock to generate quiz questions from retrieved content."""
    # Build the prompt
    existing_section = ""
    if existing_prompts:
        prompts_list = "\n".join(f"- {p}" for p in existing_prompts)
        existing_section = (
            f"\n\nThe following questions have already been generated for this "
            f"document. Generate DIFFERENT questions that do not repeat these:\n"
            f"{prompts_list}\n"
        )

    prompt = (
        "You are an expert quiz generator. Based on the following content retrieved "
        "from a course document, generate a quiz with at least 10 multiple-choice "
        "questions.\n\n"
        "Requirements:\n"
        "- Generate at least 10 questions\n"
        "- Each question must have exactly 4 answer options\n"
        "- Each question must have exactly 1 correct answer\n"
        "- The correctOptionIndex must be an integer from 0 to 3\n"
        "- Each question must have a difficulty level: easy, medium, or hard\n"
        "- Questions should cover different sections and topics from the text\n"
        "- Include a mix of difficulty levels\n"
        f"{existing_section}\n"
        "Respond ONLY with valid JSON in this exact format (no markdown, no "
        "explanation):\n"
        "{\n"
        '  "title": "Quiz title based on the content",\n'
        '  "questions": [\n'
        "    {\n"
        '      "prompt": "The question text",\n'
        '      "options": ["Option A", "Option B", "Option C", "Option D"],\n'
        '      "correctOptionIndex": 0,\n'
        '      "difficulty": "easy"\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        f"Document content:\n{retrieved_content}"
    )

    request_body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 4096,
        "temperature": 0.7,
        "messages": [
            {"role": "user", "content": prompt}
        ],
    })

    logger.info(
        "Invoking Bedrock model: %s (content length: %d chars)",
        BEDROCK_MODEL_ID,
        len(retrieved_content),
    )

    response = bedrock_runtime.invoke_model(
        modelId=BEDROCK_MODEL_ID,
        contentType="application/json",
        accept="application/json",
        body=request_body,
    )

    response_body = json.loads(response["body"].read())

    # Extract text content from Bedrock response
    content = response_body.get("content", [])
    if not content:
        raise ValueError("Empty response from Bedrock.")

    text_content = ""
    for block in content:
        if block.get("type") == "text":
            text_content += block.get("text", "")

    if not text_content:
        raise ValueError("No text content in Bedrock response.")

    return text_content


def _validate_quiz_response(raw_response):
    """Validate and parse the Bedrock quiz response.

    Returns a list of validated question dicts with questionId added.
    Raises ValueError if the response structure is invalid.
    """
    # Strip any markdown code fences if present
    cleaned = raw_response.strip()
    if cleaned.startswith("```"):
        # Remove opening fence
        first_newline = cleaned.index("\n")
        cleaned = cleaned[first_newline + 1:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    parsed = json.loads(cleaned)

    if not isinstance(parsed, dict):
        raise ValueError("Response is not a JSON object.")

    questions = parsed.get("questions")
    if not isinstance(questions, list):
        raise ValueError("Response missing 'questions' array.")

    if len(questions) < MIN_QUESTIONS:
        raise ValueError(
            f"Expected at least {MIN_QUESTIONS} questions, got {len(questions)}."
        )

    valid_difficulties = {"easy", "medium", "hard"}
    validated_questions = []

    for i, q in enumerate(questions):
        if not isinstance(q, dict):
            raise ValueError(f"Question {i} is not an object.")

        prompt = q.get("prompt")
        if not prompt or not isinstance(prompt, str):
            raise ValueError(f"Question {i} missing valid 'prompt'.")

        options = q.get("options")
        if not isinstance(options, list) or len(options) != 4:
            raise ValueError(f"Question {i} must have exactly 4 options.")

        for j, opt in enumerate(options):
            if not isinstance(opt, str) or not opt.strip():
                raise ValueError(f"Question {i}, option {j} is not a valid string.")

        correct_index = q.get("correctOptionIndex")
        if not isinstance(correct_index, int) or correct_index < 0 or correct_index > 3:
            raise ValueError(
                f"Question {i} has invalid correctOptionIndex: {correct_index}."
            )

        difficulty = q.get("difficulty", "").lower()
        if difficulty not in valid_difficulties:
            raise ValueError(
                f"Question {i} has invalid difficulty: {q.get('difficulty')}."
            )

        validated_questions.append({
            "questionId": str(uuid.uuid4()),
            "prompt": prompt.strip(),
            "options": [opt.strip() for opt in options],
            "correctOptionIndex": correct_index,
            "difficulty": difficulty,
        })

    return validated_questions


def _generate_title(file_name):
    """Generate a quiz title from the PDF file name."""
    # Remove extension
    name = file_name
    if name.lower().endswith(".pdf"):
        name = name[:-4]
    # Clean up the name
    name = name.replace("_", " ").replace("-", " ").strip()
    if not name:
        name = "Document"
    return f"Quiz: {name}"


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
