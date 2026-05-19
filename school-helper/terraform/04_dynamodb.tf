# DynamoDB Tables

# PDFs table
resource "aws_dynamodb_table" "pdfs" {
  name         = "${var.project_name}-pdfs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pdfId"

  attribute {
    name = "pdfId"
    type = "S"
  }

  attribute {
    name = "userId"
    type = "S"
  }

  attribute {
    name = "uploadedAt"
    type = "S"
  }

  global_secondary_index {
    name            = "userId-uploadedAt-index"
    hash_key        = "userId"
    range_key       = "uploadedAt"
    projection_type = "ALL"
  }

  tags = {
    Name = "${var.project_name}-pdfs"
  }
}

# Quizzes table
resource "aws_dynamodb_table" "quizzes" {
  name         = "${var.project_name}-quizzes"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "quizId"

  attribute {
    name = "quizId"
    type = "S"
  }

  attribute {
    name = "pdfId"
    type = "S"
  }

  attribute {
    name = "userId"
    type = "S"
  }

  attribute {
    name = "createdAt"
    type = "S"
  }

  global_secondary_index {
    name            = "pdfId-createdAt-index"
    hash_key        = "pdfId"
    range_key       = "createdAt"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "userId-createdAt-index"
    hash_key        = "userId"
    range_key       = "createdAt"
    projection_type = "ALL"
  }

  tags = {
    Name = "${var.project_name}-quizzes"
  }
}

# QuizAttempts table
resource "aws_dynamodb_table" "quiz_attempts" {
  name         = "${var.project_name}-quiz-attempts"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "attemptId"

  attribute {
    name = "attemptId"
    type = "S"
  }

  attribute {
    name = "userId"
    type = "S"
  }

  attribute {
    name = "quizId"
    type = "S"
  }

  attribute {
    name = "pdfId"
    type = "S"
  }

  attribute {
    name = "completedAt"
    type = "S"
  }

  global_secondary_index {
    name            = "userId-completedAt-index"
    hash_key        = "userId"
    range_key       = "completedAt"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "quizId-completedAt-index"
    hash_key        = "quizId"
    range_key       = "completedAt"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "pdfId-completedAt-index"
    hash_key        = "pdfId"
    range_key       = "completedAt"
    projection_type = "ALL"
  }

  tags = {
    Name = "${var.project_name}-quiz-attempts"
  }
}
