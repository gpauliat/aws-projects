# DynamoDB Table for the To Do List

resource "aws_dynamodb_table" "tasks" {
  name         = "${var.project_name}-tasks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "taskId"

  # Primary Key
  attribute {
    name = "taskId"
    type = "S" # String (UUID)
  }

  # GSI attribute for querying by user
  attribute {
    name = "createdBy"
    type = "S" # String (User ID)
  }

  # Global Secondary Index for querying tasks by user
  global_secondary_index {
    name            = "UserIdIndex"
    hash_key        = "createdBy"
    projection_type = "ALL"
  }

  tags = {
    Name = "${var.project_name}-tasks"
  }
}
