"""
Lambda function to remove user interest in a movie.

Idempotent operation.
"""

from botocore.exceptions import ClientError
from shared.response import no_content_response, error_response
from shared.dynamodb_client import get_dynamodb_client


def lambda_handler(event, context):
    """
    Remove user interest in a movie.
    
    Args:
        event: API Gateway event with pathParameters.movieId and Cognito user context
        context: Lambda context object
        
    Returns:
        204 No Content (idempotent)
    """
    try:
        # Extract movieId
        try:
            movie_id = event['pathParameters']['movieId']
        except (KeyError, TypeError):
            return error_response(400, "Missing movieId in path", "ValidationError")
        
        # Extract userId from Cognito
        try:
            user_claims = event['requestContext']['authorizer']['claims']
            user_id = user_claims['sub']
        except (KeyError, TypeError):
            return error_response(401, "Unauthorized - missing user context", "AuthError")
        
        db_client = get_dynamodb_client()
        
        # Delete interest (idempotent - no error if doesn't exist)
        try:
            db_client.interests_table.delete_item(
                Key={
                    'userId': user_id,
                    'movieId': movie_id
                }
            )
            return no_content_response()
            
        except ClientError as e:
            status_code, error_msg = db_client.handle_client_error(e)
            return error_response(status_code, error_msg, "DatabaseError")
        
    except Exception as e:
        print(f"Unexpected error in removeInterest: {str(e)}")
        return error_response(500, "Internal server error", "ServerError")
