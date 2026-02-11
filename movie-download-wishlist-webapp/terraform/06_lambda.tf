# Lambda Functions Infrastructure

# Data source to package Lambda functions
data "archive_file" "lambda_package" {
  type        = "zip"
  source_dir  = "${path.module}/../lambda/src"
  output_path = "${path.module}/../lambda/lambda_package.zip"
}

# Lambda Function: Create Movie
resource "aws_lambda_function" "create_movie" {
  filename         = data.archive_file.lambda_package.output_path
  function_name    = "${var.project_name}-${var.environment}-create-movie"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "create_movie.lambda_handler"
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 512

  environment {
    variables = {
      MOVIES_TABLE_NAME    = aws_dynamodb_table.movies.name
      INTERESTS_TABLE_NAME = aws_dynamodb_table.interests.name
      USER_POOL_ID         = aws_cognito_user_pool.main.id
    }
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-create-movie"
  }
}

# Lambda Function: Get Movies
resource "aws_lambda_function" "get_movies" {
  filename         = data.archive_file.lambda_package.output_path
  function_name    = "${var.project_name}-${var.environment}-get-movies"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "get_movies.lambda_handler"
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 512

  environment {
    variables = {
      MOVIES_TABLE_NAME    = aws_dynamodb_table.movies.name
      INTERESTS_TABLE_NAME = aws_dynamodb_table.interests.name
      USER_POOL_ID         = aws_cognito_user_pool.main.id
    }
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-get-movies"
  }
}

# Lambda Function: Update Movie Status
resource "aws_lambda_function" "update_movie_status" {
  filename         = data.archive_file.lambda_package.output_path
  function_name    = "${var.project_name}-${var.environment}-update-movie-status"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "update_movie_status.lambda_handler"
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 512

  environment {
    variables = {
      MOVIES_TABLE_NAME    = aws_dynamodb_table.movies.name
      INTERESTS_TABLE_NAME = aws_dynamodb_table.interests.name
      USER_POOL_ID         = aws_cognito_user_pool.main.id
    }
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-update-movie-status"
  }
}

# Lambda Function: Delete Movie
resource "aws_lambda_function" "delete_movie" {
  filename         = data.archive_file.lambda_package.output_path
  function_name    = "${var.project_name}-${var.environment}-delete-movie"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "delete_movie.lambda_handler"
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 512

  environment {
    variables = {
      MOVIES_TABLE_NAME    = aws_dynamodb_table.movies.name
      INTERESTS_TABLE_NAME = aws_dynamodb_table.interests.name
      USER_POOL_ID         = aws_cognito_user_pool.main.id
    }
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-delete-movie"
  }
}

# Lambda Function: Add Interest
resource "aws_lambda_function" "add_interest" {
  filename         = data.archive_file.lambda_package.output_path
  function_name    = "${var.project_name}-${var.environment}-add-interest"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "add_interest.lambda_handler"
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 512

  environment {
    variables = {
      MOVIES_TABLE_NAME    = aws_dynamodb_table.movies.name
      INTERESTS_TABLE_NAME = aws_dynamodb_table.interests.name
      USER_POOL_ID         = aws_cognito_user_pool.main.id
    }
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-add-interest"
  }
}

# Lambda Function: Remove Interest
resource "aws_lambda_function" "remove_interest" {
  filename         = data.archive_file.lambda_package.output_path
  function_name    = "${var.project_name}-${var.environment}-remove-interest"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "remove_interest.lambda_handler"
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 512

  environment {
    variables = {
      MOVIES_TABLE_NAME    = aws_dynamodb_table.movies.name
      INTERESTS_TABLE_NAME = aws_dynamodb_table.interests.name
      USER_POOL_ID         = aws_cognito_user_pool.main.id
    }
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-remove-interest"
  }
}

# Lambda Function: Get Interested Users
resource "aws_lambda_function" "get_interested_users" {
  filename         = data.archive_file.lambda_package.output_path
  function_name    = "${var.project_name}-${var.environment}-get-interested-users"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "get_interested_users.lambda_handler"
  source_code_hash = data.archive_file.lambda_package.output_base64sha256
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 512

  environment {
    variables = {
      MOVIES_TABLE_NAME    = aws_dynamodb_table.movies.name
      INTERESTS_TABLE_NAME = aws_dynamodb_table.interests.name
      USER_POOL_ID         = aws_cognito_user_pool.main.id
    }
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-get-interested-users"
  }
}

# CloudWatch Log Groups for Lambda Functions
resource "aws_cloudwatch_log_group" "create_movie" {
  name              = "/aws/lambda/${aws_lambda_function.create_movie.function_name}"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-${var.environment}-create-movie-logs"
  }
}

resource "aws_cloudwatch_log_group" "get_movies" {
  name              = "/aws/lambda/${aws_lambda_function.get_movies.function_name}"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-${var.environment}-get-movies-logs"
  }
}

resource "aws_cloudwatch_log_group" "update_movie_status" {
  name              = "/aws/lambda/${aws_lambda_function.update_movie_status.function_name}"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-${var.environment}-update-movie-status-logs"
  }
}

resource "aws_cloudwatch_log_group" "delete_movie" {
  name              = "/aws/lambda/${aws_lambda_function.delete_movie.function_name}"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-${var.environment}-delete-movie-logs"
  }
}

resource "aws_cloudwatch_log_group" "add_interest" {
  name              = "/aws/lambda/${aws_lambda_function.add_interest.function_name}"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-${var.environment}-add-interest-logs"
  }
}

resource "aws_cloudwatch_log_group" "remove_interest" {
  name              = "/aws/lambda/${aws_lambda_function.remove_interest.function_name}"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-${var.environment}-remove-interest-logs"
  }
}

resource "aws_cloudwatch_log_group" "get_interested_users" {
  name              = "/aws/lambda/${aws_lambda_function.get_interested_users.function_name}"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-${var.environment}-get-interested-users-logs"
  }
}
