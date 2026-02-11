# DynamoDB Tables for Movie Download Wishlist

# Movies Table
resource "aws_dynamodb_table" "movies" {
  name         = "${var.project_name}-${var.environment}-movies"
  billing_mode = var.dynamodb_billing_mode
  hash_key     = "movieId"

  # Primary Key
  attribute {
    name = "movieId"
    type = "S" # String (UUID)
  }

  # Point-in-time recovery for data protection
  point_in_time_recovery {
    enabled = var.enable_dynamodb_point_in_time_recovery
  }

  # Server-side encryption at rest
  server_side_encryption {
    enabled = true
  }

  # TTL disabled (we want to keep all movies)
  ttl {
    enabled = false
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-movies"
  }
}

# Interests Table
resource "aws_dynamodb_table" "interests" {
  name         = "${var.project_name}-${var.environment}-interests"
  billing_mode = var.dynamodb_billing_mode
  hash_key     = "userId"
  range_key    = "movieId"

  # Primary Key Attributes
  attribute {
    name = "userId"
    type = "S" # String (Cognito user sub)
  }

  attribute {
    name = "movieId"
    type = "S" # String (UUID)
  }

  # Global Secondary Index for querying interests by movie
  global_secondary_index {
    name            = "MovieInterestsIndex"
    hash_key        = "movieId"
    range_key       = "userId"
    projection_type = "ALL"
  }

  # Point-in-time recovery for data protection
  point_in_time_recovery {
    enabled = var.enable_dynamodb_point_in_time_recovery
  }

  # Server-side encryption at rest
  server_side_encryption {
    enabled = true
  }

  # TTL disabled (we want to keep all interests)
  ttl {
    enabled = false
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-interests"
  }
}
