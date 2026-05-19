# Lambda IAM Roles, Policies, and CloudWatch Log Groups

# Shared assume role policy for all Lambda functions
data "aws_iam_policy_document" "assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# ---------------------------------------------------------------------------
# CloudWatch Log Groups (7-day retention)
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "pdf_upload" {
  name              = "/aws/lambda/${var.project_name}-pdf-upload"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "kb_sync" {
  name              = "/aws/lambda/${var.project_name}-kb-sync"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "quiz_generation" {
  name              = "/aws/lambda/${var.project_name}-quiz-generation"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "quiz_taking" {
  name              = "/aws/lambda/${var.project_name}-quiz-taking"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "history" {
  name              = "/aws/lambda/${var.project_name}-history"
  retention_in_days = 7
}

resource "aws_cloudwatch_log_group" "management" {
  name              = "/aws/lambda/${var.project_name}-management"
  retention_in_days = 7
}

# ---------------------------------------------------------------------------
# IAM Roles
# ---------------------------------------------------------------------------

resource "aws_iam_role" "pdf_upload" {
  name               = "${var.project_name}-pdf-upload-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_iam_role" "kb_sync" {
  name               = "${var.project_name}-kb-sync-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_iam_role" "quiz_generation" {
  name               = "${var.project_name}-quiz-generation-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_iam_role" "quiz_taking" {
  name               = "${var.project_name}-quiz-taking-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_iam_role" "history" {
  name               = "${var.project_name}-history-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_iam_role" "management" {
  name               = "${var.project_name}-management-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

# ---------------------------------------------------------------------------
# IAM Policies — PDF Upload Lambda
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "pdf_upload" {
  # CloudWatch Logs
  statement {
    effect    = "Allow"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.pdf_upload.arn}:*"]
  }

  # S3 — generate presigned PUT URLs
  statement {
    effect    = "Allow"
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.pdf_storage.arn}/pdfs/*"]
  }

  # DynamoDB — create PDF record
  statement {
    effect    = "Allow"
    actions   = ["dynamodb:PutItem"]
    resources = [aws_dynamodb_table.pdfs.arn]
  }
}

resource "aws_iam_role_policy" "pdf_upload" {
  name   = "${var.project_name}-pdf-upload-policy"
  role   = aws_iam_role.pdf_upload.id
  policy = data.aws_iam_policy_document.pdf_upload.json
}

# ---------------------------------------------------------------------------
# IAM Policies — Knowledge Base Sync Lambda
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "kb_sync" {
  # CloudWatch Logs
  statement {
    effect    = "Allow"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.kb_sync.arn}:*"]
  }

  # DynamoDB — update PDF record with sync status
  statement {
    effect    = "Allow"
    actions   = ["dynamodb:GetItem", "dynamodb:UpdateItem"]
    resources = [aws_dynamodb_table.pdfs.arn]
  }

  # Bedrock — start and monitor Knowledge Base ingestion jobs
  statement {
    effect    = "Allow"
    actions   = ["bedrock:StartIngestionJob", "bedrock:GetIngestionJob"]
    resources = [aws_bedrockagent_knowledge_base.this.arn]
  }
}

resource "aws_iam_role_policy" "kb_sync" {
  name   = "${var.project_name}-kb-sync-policy"
  role   = aws_iam_role.kb_sync.id
  policy = data.aws_iam_policy_document.kb_sync.json
}

# ---------------------------------------------------------------------------
# IAM Policies — Quiz Generation Lambda
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "quiz_generation" {
  # CloudWatch Logs
  statement {
    effect    = "Allow"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.quiz_generation.arn}:*"]
  }

  # DynamoDB — read PDF text, read existing quizzes, write new quiz, update quiz count
  statement {
    effect  = "Allow"
    actions = ["dynamodb:GetItem", "dynamodb:UpdateItem", "dynamodb:PutItem", "dynamodb:Query"]
    resources = [
      aws_dynamodb_table.pdfs.arn,
      aws_dynamodb_table.quizzes.arn,
      "${aws_dynamodb_table.quizzes.arn}/index/*",
    ]
  }

  # Bedrock — invoke model for quiz generation (direct + cross-region inference)
  statement {
    effect    = "Allow"
    actions   = ["bedrock:InvokeModel"]
    resources = [
      "arn:aws:bedrock:${var.aws_region}::foundation-model/*",
      "arn:aws:bedrock:${var.aws_region}::inference-profile/*",
      "arn:aws:bedrock:${var.aws_region}:${data.aws_caller_identity.current.account_id}:inference-profile/*",
      "arn:aws:bedrock:eu-west-1::foundation-model/*",
      "arn:aws:bedrock:eu-west-2::foundation-model/*",
      "arn:aws:bedrock:eu-west-3::foundation-model/*",
      "arn:aws:bedrock:eu-central-1::foundation-model/*",
      "arn:aws:bedrock:eu-central-2::foundation-model/*",
      "arn:aws:bedrock:eu-north-1::foundation-model/*",
      "arn:aws:bedrock:eu-south-1::foundation-model/*",
      "arn:aws:bedrock:eu-south-2::foundation-model/*",
    ]
  }

  # Bedrock — retrieve content from Knowledge Base
  statement {
    effect    = "Allow"
    actions   = ["bedrock:Retrieve"]
    resources = [aws_bedrockagent_knowledge_base.this.arn]
  }
}

resource "aws_iam_role_policy" "quiz_generation" {
  name   = "${var.project_name}-quiz-generation-policy"
  role   = aws_iam_role.quiz_generation.id
  policy = data.aws_iam_policy_document.quiz_generation.json
}

# ---------------------------------------------------------------------------
# IAM Policies — Quiz Taking Lambda
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "quiz_taking" {
  # CloudWatch Logs
  statement {
    effect    = "Allow"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.quiz_taking.arn}:*"]
  }

  # DynamoDB — read quizzes, write quiz attempts
  statement {
    effect  = "Allow"
    actions = ["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:Query"]
    resources = [
      aws_dynamodb_table.quizzes.arn,
      "${aws_dynamodb_table.quizzes.arn}/index/*",
      aws_dynamodb_table.quiz_attempts.arn,
    ]
  }
}

resource "aws_iam_role_policy" "quiz_taking" {
  name   = "${var.project_name}-quiz-taking-policy"
  role   = aws_iam_role.quiz_taking.id
  policy = data.aws_iam_policy_document.quiz_taking.json
}

# ---------------------------------------------------------------------------
# IAM Policies — History Lambda
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "history" {
  # CloudWatch Logs
  statement {
    effect    = "Allow"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.history.arn}:*"]
  }

  # DynamoDB — read quiz attempts, quizzes, and PDFs for history/progress
  statement {
    effect  = "Allow"
    actions = ["dynamodb:GetItem", "dynamodb:Query"]
    resources = [
      aws_dynamodb_table.quiz_attempts.arn,
      "${aws_dynamodb_table.quiz_attempts.arn}/index/*",
      aws_dynamodb_table.quizzes.arn,
      aws_dynamodb_table.pdfs.arn,
    ]
  }
}

resource "aws_iam_role_policy" "history" {
  name   = "${var.project_name}-history-policy"
  role   = aws_iam_role.history.id
  policy = data.aws_iam_policy_document.history.json
}

# ---------------------------------------------------------------------------
# IAM Policies — Management Lambda
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "management" {
  # CloudWatch Logs
  statement {
    effect    = "Allow"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["${aws_cloudwatch_log_group.management.arn}:*"]
  }

  # S3 — delete PDF files
  statement {
    effect    = "Allow"
    actions   = ["s3:DeleteObject"]
    resources = ["${aws_s3_bucket.pdf_storage.arn}/pdfs/*"]
  }

  # DynamoDB — CRUD on PDFs, Quizzes, QuizAttempts for cascade deletion
  statement {
    effect  = "Allow"
    actions = ["dynamodb:GetItem", "dynamodb:DeleteItem", "dynamodb:Query", "dynamodb:BatchWriteItem"]
    resources = [
      aws_dynamodb_table.pdfs.arn,
      "${aws_dynamodb_table.pdfs.arn}/index/*",
      aws_dynamodb_table.quizzes.arn,
      "${aws_dynamodb_table.quizzes.arn}/index/*",
      aws_dynamodb_table.quiz_attempts.arn,
      "${aws_dynamodb_table.quiz_attempts.arn}/index/*",
    ]
  }
}

resource "aws_iam_role_policy" "management" {
  name   = "${var.project_name}-management-policy"
  role   = aws_iam_role.management.id
  policy = data.aws_iam_policy_document.management.json
}
