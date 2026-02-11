"""
Lambda function to delete a movie and its associated interests.

Uses DynamoDB transactions for atomicity.
"""

from botocore.exceptions import ClientError
from shared.response import no_content_response, error_response
from shared.dynamodb_client import get_dynamodb_client


def lambda_handler(event, context):
    """
    Delete a movie and all associated interests.
    
    Args:
        event: API Gateway event with pathParameters.movieId
        context: Lambda context object
        
    Returns:
        204 No Content or error
    """
    try:
        # Extract movieId
        try:
            movie_id = event['pathParameters']['movieId']
        except (KeyError, TypeError):
            return error_response(400, "Missing movieId in path", "ValidationError")
        
        db_client = get_dynamodb_client()
        
        # Query all interests for this movie
        try:
            interests_response = db_client.interests_table.query(
                IndexName='MovieInterestsIndex',
                KeyConditionExpression='movieId = :movieId',
                ExpressionAttributeValues={':movieId': movie_id}
            )
            interests = interests_response.get('Items', [])
        except ClientError as e:
            status_code, error_msg = db_client.handle_client_error(e)
            return error_response(status_code, error_msg, "DatabaseError")
        
        # Build transaction items
        transact_items = [
            {
                'Delete': {
                    'TableName': db_client.movies_table_name,
                    'Key': {'movieId': movie_id},
                    'ConditionExpression': 'attribute_exists(movieId)'
                }
            }
        ]
        
        # Add delete for each interest
        for interest in interests:
            transact_items.append({
                'Delete': {
                    'TableName': db_client.interests_table_name,
                    'Key': {
                        'userId': interest['userId'],
                        'movieId': interest['movieId']
                    }
                }
            })
        
        # Execute transaction
        try:
            db_client.dynamodb.meta.client.transact_write_items(
                TransactItems=transact_items
            )
            return no_content_response()
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'TransactionCanceledException':
                # Check if movie didn't exist
                cancellation_reasons = e.response.get('CancellationReasons', [])
                if not cancellation_reasons:
                    # Try to get from Error dict
                    error_message = e.response['Error'].get('Message', '')
                    if 'ConditionalCheckFailed' in error_message or 'ConditionalCheckFailedException' in error_message:
                        return error_response(404, "Movie not found", "NotFoundError")
                elif cancellation_reasons[0].get('Code') == 'ConditionalCheckFailed':
                    return error_response(404, "Movie not found", "NotFoundError")
                return error_response(500, "Transaction failed", "TransactionError")
            elif error_code == 'ConditionalCheckFailedException':
                return error_response(404, "Movie not found", "NotFoundError")
            
            status_code, error_msg = db_client.handle_client_error(e)
            return error_response(status_code, error_msg, "DatabaseError")
        
    except Exception as e:
        print(f"Unexpected error in deleteMovie: {str(e)}")
        return error_response(500, "Internal server error", "ServerError")
