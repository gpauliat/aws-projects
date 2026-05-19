# Quiz Taking Lambda

data "archive_file" "quiz_taking" {
  type        = "zip"
  source_file = "${path.module}/lambdas/quiz_taking/lambda_function.py"
  output_path = "${path.module}/.build/quiz_taking.zip"
}

resource "aws_lambda_function" "quiz_taking" {
  function_name    = "${var.project_name}-quiz-taking"
  role             = aws_iam_role.quiz_taking.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.11"
  timeout          = 30
  filename         = data.archive_file.quiz_taking.output_path
  source_code_hash = data.archive_file.quiz_taking.output_base64sha256

  environment {
    variables = {
      DYNAMODB_QUIZZES_TABLE_NAME       = aws_dynamodb_table.quizzes.name
      DYNAMODB_QUIZ_ATTEMPTS_TABLE_NAME = aws_dynamodb_table.quiz_attempts.name
    }
  }

  depends_on = [
    aws_iam_role_policy.quiz_taking,
    aws_cloudwatch_log_group.quiz_taking,
  ]

  tags = {
    Name = "${var.project_name}-quiz-taking"
  }
}
