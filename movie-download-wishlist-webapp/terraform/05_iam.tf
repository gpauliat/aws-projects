# IAM Roles and Policies for Lambda Functions

# Lambda Execution Role
resource "aws_iam_role" "lambda_execution" {
  name = "${var.project_name}-${var.environment}-lambda-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-lambda-execution-role"
  }
}

# Attach AWS managed policy for CloudWatch Logs
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Custom policy for DynamoDB access
resource "aws_iam_policy" "lambda_dynamodb" {
  name        = "${var.project_name}-${var.environment}-lambda-dynamodb-policy"
  description = "Policy for Lambda functions to access DynamoDB tables"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.movies.arn,
          aws_dynamodb_table.interests.arn,
          "${aws_dynamodb_table.interests.arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:TransactWriteItems"
        ]
        Resource = [
          aws_dynamodb_table.movies.arn,
          aws_dynamodb_table.interests.arn
        ]
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-lambda-dynamodb-policy"
  }
}

# Attach DynamoDB policy to Lambda execution role
resource "aws_iam_role_policy_attachment" "lambda_dynamodb" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = aws_iam_policy.lambda_dynamodb.arn
}

# Custom policy for Cognito access
resource "aws_iam_policy" "lambda_cognito" {
  name        = "${var.project_name}-${var.environment}-lambda-cognito-policy"
  description = "Policy for Lambda functions to access Cognito User Pool"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cognito-idp:AdminGetUser",
          "cognito-idp:ListUsers"
        ]
        Resource = aws_cognito_user_pool.main.arn
      }
    ]
  })

  tags = {
    Name = "${var.project_name}-${var.environment}-lambda-cognito-policy"
  }
}

# Attach Cognito policy to Lambda execution role
resource "aws_iam_role_policy_attachment" "lambda_cognito" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = aws_iam_policy.lambda_cognito.arn
}
