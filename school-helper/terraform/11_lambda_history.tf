# History Lambda

data "archive_file" "history" {
  type        = "zip"
  source_file = "${path.module}/lambdas/history/lambda_function.py"
  output_path = "${path.module}/.build/history.zip"
}

resource "aws_lambda_function" "history" {
  function_name    = "${var.project_name}-history"
  role             = aws_iam_role.history.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.11"
  timeout          = 30
  filename         = data.archive_file.history.output_path
  source_code_hash = data.archive_file.history.output_base64sha256

  environment {
    variables = {
      DYNAMODB_QUIZ_ATTEMPTS_TABLE_NAME = aws_dynamodb_table.quiz_attempts.name
      DYNAMODB_QUIZZES_TABLE_NAME       = aws_dynamodb_table.quizzes.name
      DYNAMODB_PDFS_TABLE_NAME          = aws_dynamodb_table.pdfs.name
    }
  }

  depends_on = [
    aws_iam_role_policy.history,
    aws_cloudwatch_log_group.history,
  ]

  tags = {
    Name = "${var.project_name}-history"
  }
}
