# Quiz Generation Lambda

data "archive_file" "quiz_generation" {
  type        = "zip"
  source_file = "${path.module}/lambdas/quiz_generation/lambda_function.py"
  output_path = "${path.module}/.build/quiz_generation.zip"
}

resource "aws_lambda_function" "quiz_generation" {
  function_name    = "${var.project_name}-quiz-generation"
  role             = aws_iam_role.quiz_generation.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.11"
  timeout          = 300
  filename         = data.archive_file.quiz_generation.output_path
  source_code_hash = data.archive_file.quiz_generation.output_base64sha256

  environment {
    variables = {
      DYNAMODB_PDFS_TABLE_NAME    = aws_dynamodb_table.pdfs.name
      DYNAMODB_QUIZZES_TABLE_NAME = aws_dynamodb_table.quizzes.name
      BEDROCK_MODEL_ID            = "eu.anthropic.claude-haiku-4-5-20251001-v1:0"
      KNOWLEDGE_BASE_ID           = aws_bedrockagent_knowledge_base.this.id
      S3_BUCKET_NAME              = aws_s3_bucket.pdf_storage.id
    }
  }

  depends_on = [
    aws_iam_role_policy.quiz_generation,
    aws_cloudwatch_log_group.quiz_generation,
  ]

  tags = {
    Name = "${var.project_name}-quiz-generation"
  }
}
