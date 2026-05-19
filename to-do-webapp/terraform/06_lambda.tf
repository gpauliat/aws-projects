# Lambda Functions Infrastructure

# Data source to package Lambda functions
data "archive_file" "lambda_package" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/src"
  output_path = "${path.module}/../lambda/lambda_package.zip"
}

# Lambda Function: Create task
resource "aws_lambda_function" "create_task" {
  filename         = data.archive_file.lambda_package.output_path
  function_name    = "${var.project_name}-create-task"
  role             = aws_iam_role.lambda_execution.arn
  handler          = "create_task.lambda_handler"
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  runtime          = "python3.11"
  timeout          = 30
  memory_size      = 512

  environment {
    variables = {
      TASKS_TABLE_NAME     = aws_dynamodb_table.tasks.name
      INTERESTS_TABLE_NAME = aws_dynamodb_table.interests.name
      USER_POOL_ID         = aws_cognito_user_pool.main.id
    }
  }

  tags = {
    Name = "${var.project_name}-create-task"
  }
}

# Lambda Function: Get tasks
resource "aws_lambda_function" "get_tasks" {
  filename          = data.archive_file.lambda_package.output_path
  function_name     = "${var.project_name}-get-tasks"
  role              = aws_iam_role.lambda_execution.arn
  handler           = "get_tasks.lambda_handler"
  source_code_hash  = data.archive_file.lambda_package.output_base64sha256
  runtime           = "python3.11"
  timeout           = 30
  memory_size       = 512

  environment {
    variables = {
      TASKS_TABLE_NAME     = aws_dynamodb_table.tasks.name
      INTERESTS_TABLE_NAME = aws_dynamodb_table.interests.name
      USER_POOL_ID         = aws_cognito_user_pool.main.id
    }
  }

  tags = {
    Name = "${var.project_name}-get-tasks"
  }
}

# Lambda Function: Update task
resource "aws_lambda_function" "update_task" {
  filename         = data.archive_file.lambda_package.output_path
  function_name    = "${var.project_name}-update-task"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "update_task.lambda_handler"
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 512

  environment {
    variables = {
      TASKS_TABLE_NAME     = aws_dynamodb_table.tasks.name
      INTERESTS_TABLE_NAME = aws_dynamodb_table.interests.name
      USER_POOL_ID         = aws_cognito_user_pool.main.id
    }
  }

  tags = {
    Name = "${var.project_name}-update-task"
  }
}

# Lambda Function: Delete task
resource "aws_lambda_function" "delete_task" {
  filename         = data.archive_file.lambda_package.output_path
  function_name    = "${var.project_name}-delete-task"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "delete_task.lambda_handler"
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 512

  environment {
    variables = {
      TASKS_TABLE_NAME    = aws_dynamodb_table.tasks.name
      INTERESTS_TABLE_NAME = aws_dynamodb_table.interests.name
      USER_POOL_ID         = aws_cognito_user_pool.main.id
    }
  }

  tags = {
    Name = "${var.project_name}-delete-task"
  }
}

# CloudWatch Log Groups for Lambda Functions
resource "aws_cloudwatch_log_group" "create_task" {
  name              = "/aws/lambda/${aws_lambda_function.create_task.function_name}"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-create-task-logs"
  }
}

resource "aws_cloudwatch_log_group" "get_tasks" {
  name              = "/aws/lambda/${aws_lambda_function.get_tasks.function_name}"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-get-tasks-logs"
  }
}

resource "aws_cloudwatch_log_group" "update_task" {
  name              = "/aws/lambda/${aws_lambda_function.update_task.function_name}"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-update-task-logs"
  }
}

resource "aws_cloudwatch_log_group" "delete_task" {
  name              = "/aws/lambda/${aws_lambda_function.delete_task.function_name}"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-delete-task-logs"
  }
}