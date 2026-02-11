"""
Lambda function to add user interest in a movie.
"""

import time
from botocore.exceptions import ClientError
from shared.response import success_response, error_response
from shared.dynamodb_client import get_dynamodb_client


def lambda_handler(event, context):
    """
    Add user interest in a movie.
    
    Args:
        event: API Gateway event with pathParameters.movieId and Cognito user context
        context: Lambda context object
        
    Returns:
        201 Created with interest or error
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
        
        # Verify movie exists
        try:
            movie_response = db_client.movies_table.get_item(Key={'movieId': movie_id})
            if 'Item' not in movie_response:
                return error_response(404, "Movie not found", "NotFoundError")
        except ClientError as e:
            status_code, error_msg = db_client.handle_client_error(e)
            return error_response(status_code, error_msg, "DatabaseError")
        
        # Create interest (idempotent - no error if already exists)
        current_time = int(time.time())
        interest_item = {
            'userId': user_id,
            'movieId': movie_id,
            'createdAt': current_time
        }
        
        try:
            db_client.interests_table.put_item(Item=interest_item)
            return success_response(201, interest_item)
            
        except ClientError as e:
            status_code, error_msg = db_client.handle_client_error(e)
            return error_response(status_code, error_msg, "DatabaseError")
        
    except Exception as e:
        print(f"Unexpected error in addInterest: {str(e)}")
        return error_response(500, "Internal server error", "ServerError")
