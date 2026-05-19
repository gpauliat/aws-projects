"""
Lambda function to update a task.

This function:
- Validates the task exists and belongs to the user
- Updates task status or title
- Returns the updated task
"""

import json
import time
from botocore.exceptions import ClientError

from shared.response import success_response, error_response
from shared.dynamodb_client import get_dynamodb_client
from shared.validation import validate_task_title


def lambda_handler(event, context):
    """
    Update a task's status or title.
    
    Args:
        event: API Gateway event containing:
            - pathParameters.taskId: Task ID to update
            - body: JSON with 'status' and/or 'title' fields
            - requestContext.authorizer.claims: Cognito user info
        context: Lambda context object
        
    Returns:
        API Gateway response with updated task or error
    """
    try:
        # Extract taskId
        try:
            task_id = event['pathParameters']['taskId']
        except (KeyError, TypeError):
            return error_response(400, "Missing taskId in path", "ValidationError")
        
        # Parse request body
        try:
            body = json.loads(event.get('body', '{}'))
        except json.JSONDecodeError:
            return error_response(400, "Invalid JSON in request body", "ValidationError")
        
        # Extract userId from Cognito context
        try:
            user_claims = event['requestContext']['authorizer']['claims']
            user_id = user_claims['sub']
        except (KeyError, TypeError):
            return error_response(401, "Unauthorized - missing user context", "AuthError")
        
        # Extract fields to update
        new_status = body.get('status')
        new_title = body.get('title')
        
        # Validate at least one field is provided
        if new_status is None and new_title is None:
            return error_response(400, "Must provide 'status' or 'title' to update", "ValidationError")
        
        # Validate status if provided
        if new_status is not None and new_status not in ['todo', 'in-progress', 'done']:
            return error_response(400, "Invalid status. Must be 'todo', 'in-progress', or 'done'", "ValidationError")
        
        # Validate title if provided
        if new_title is not None:
            is_valid, error_message = validate_task_title(new_title)
            if not is_valid:
                return error_response(400, error_message, "ValidationError")
        
        # Build update expression
        update_parts = []
        expression_values = {':userId': user_id, ':updatedAt': int(time.time())}
        
        if new_status is not None:
            update_parts.append('status = :status')
            expression_values[':status'] = new_status
        
        if new_title is not None:
            update_parts.append('title = :title')
            expression_values[':title'] = new_title.strip()
        
        update_parts.append('updatedAt = :updatedAt')
        
        update_expression = 'SET ' + ', '.join(update_parts)
        
        # Update task in DynamoDB with ownership check
        try:
            db_client = get_dynamodb_client()
            response = db_client.tasks_table.update_item(
                Key={'taskId': task_id},
                UpdateExpression=update_expression,
                ConditionExpression='attribute_exists(taskId) AND createdBy = :userId',
                ExpressionAttributeValues=expression_values,
                ReturnValues='ALL_NEW'
            )
            
            updated_task = response.get('Attributes', {})
            return success_response(200, updated_task)
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ConditionalCheckFailedException':
                return error_response(404, "Task not found or you don't have permission to update it", "NotFoundError")
            
            status_code, error_msg = db_client.handle_client_error(e)
            return error_response(status_code, error_msg, "DatabaseError")
        
    except Exception as e:
        print(f"Unexpected error in updateTask: {str(e)}")
        return error_response(500, "Internal server error", "ServerError")
