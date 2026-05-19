# Management Lambda

data "archive_file" "management" {
  type        = "zip"
  source_file = "${path.module}/lambdas/management/lambda_function.py"
  output_path = "${path.module}/.build/management.zip"
}

resource "aws_lambda_function" "management" {
  function_name    = "${var.project_name}-management"
  role             = aws_iam_role.management.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.11"
  timeout          = 60
  filename         = data.archive_file.management.output_path
  source_code_hash = data.archive_file.management.output_base64sha256

  environment {
    variables = {
      DYNAMODB_PDFS_TABLE_NAME          = aws_dynamodb_table.pdfs.name
      DYNAMODB_QUIZZES_TABLE_NAME       = aws_dynamodb_table.quizzes.name
      DYNAMODB_QUIZ_ATTEMPTS_TABLE_NAME = aws_dynamodb_table.quiz_attempts.name
      S3_BUCKET_NAME                    = aws_s3_bucket.pdf_storage.id
    }
  }

  depends_on = [
    aws_iam_role_policy.management,
    aws_cloudwatch_log_group.management,
  ]

  tags = {
    Name = "${var.project_name}-management"
  }
}
