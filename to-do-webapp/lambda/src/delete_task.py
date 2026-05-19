"""
Lambda function to delete a task.

Uses DynamoDB transactions for atomicity.
"""

from botocore.exceptions import ClientError
from shared.response import no_content_response, error_response
from shared.dynamodb_client import get_dynamodb_client


def lambda_handler(event, context):
    """
    Delete a task.
    
    Args:
        event: API Gateway event with pathParameters.taskId
        context: Lambda context object
        
    Returns:
        204 No Content or error
    """
    try:
        # Extract taskId
        try:
            task_id = event['pathParameters']['taskId']
        except (KeyError, TypeError):
            return error_response(400, "Missing taskId in path", "ValidationError")
        
        # Extract userId from Cognito context
        try:
            user_claims = event['requestContext']['authorizer']['claims']
            user_id = user_claims['sub']
        except (KeyError, TypeError):
            return error_response(401, "Unauthorized - missing user context", "AuthError")
        
        db_client = get_dynamodb_client()
        
        # Build transaction items with ownership check
        transact_items = [
            {
                'Delete': {
                    'TableName': db_client.tasks_table_name,
                    'Key': {'taskId': task_id},
                    'ConditionExpression': 'attribute_exists(taskId) AND createdBy = :userId',
                    'ExpressionAttributeValues': {
                        ':userId': user_id
                    }
                }
            }
        ]

        # Execute transaction
        try:
            db_client.dynamodb.meta.client.transact_write_items(
                TransactItems=transact_items
            )
            return no_content_response()
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'TransactionCanceledException':
                # Check if task didn't exist
                cancellation_reasons = e.response.get('CancellationReasons', [])
                if not cancellation_reasons:
                    # Try to get from Error dict
                    error_message = e.response['Error'].get('Message', '')
                    if 'ConditionalCheckFailed' in error_message or 'ConditionalCheckFailedException' in error_message:
                        return error_response(404, "Task not found", "NotFoundError")
                elif cancellation_reasons[0].get('Code') == 'ConditionalCheckFailed':
                    return error_response(404, "Task not found", "NotFoundError")
                return error_response(500, "Transaction failed", "TransactionError")
            elif error_code == 'ConditionalCheckFailedException':
                return error_response(404, "Task not found", "NotFoundError")
            
            status_code, error_msg = db_client.handle_client_error(e)
            return error_response(status_code, error_msg, "DatabaseError")
        
    except Exception as e:
        print(f"Unexpected error in deleteTask: {str(e)}")
        return error_response(500, "Internal server error", "ServerError")
