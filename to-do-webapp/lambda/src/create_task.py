"""
Lambda function to create a new task.

This function:
- Validates the task title is non-empty
- Generates a unique taskId (UUID)
- Creates a DynamoDB item with progress status
- Returns the created task or validation error
"""

import json
import uuid
import time
from botocore.exceptions import ClientError

from shared.response import success_response, error_response
from shared.dynamodb_client import get_dynamodb_client
from shared.validation import validate_task_title


def lambda_handler(event, context):
    """
    Create a new task.
    
    Args:
        event: API Gateway event containing:
            - body: JSON with 'title' field
            - requestContext.authorizer.claims: Cognito user info
        context: Lambda context object
        
    Returns:
        API Gateway response with created task or error
    """
    try:
        # Parse request body
        try:
            body = json.loads(event.get('body', '{}'))
        except json.JSONDecodeError:
            return error_response(400, "Invalid JSON in request body", "ValidationError")
        
        # Extract title from body
        title = body.get('title')
        
        # Validate title
        is_valid, error_message = validate_task_title(title)
        if not is_valid:
            return error_response(400, error_message, "ValidationError")
        
        # Extract userId from Cognito context
        try:
            user_claims = event['requestContext']['authorizer']['claims']
            user_id = user_claims['sub']
        except (KeyError, TypeError):
            return error_response(401, "Unauthorized - missing user context", "AuthError")
        
        # Generate unique taskId
        task_id = str(uuid.uuid4())
        
        # Get current timestamp
        current_time = int(time.time())
        
        # Create task item
        task_item = {
            'taskId': task_id,
            'title': title.strip(),
            'status': 'todo',
            'createdBy': user_id,
            'createdAt': current_time,
            'updatedAt': current_time
        }
        
        # Save to DynamoDB
        try:
            db_client = get_dynamodb_client()
            db_client.tasks_table.put_item(Item=task_item)
            
        except ClientError as e:
            status_code, error_msg = db_client.handle_client_error(e)
            return error_response(status_code, error_msg, "DatabaseError")
        except Exception as e:
            print(f"Unexpected error creating task: {str(e)}")
            return error_response(500, "Internal server error", "ServerError")
        
        # Return created task
        return success_response(201, task_item)
        
    except Exception as e:
        print(f"Unexpected error in createTask: {str(e)}")
        return error_response(500, "Internal server error", "ServerError")
