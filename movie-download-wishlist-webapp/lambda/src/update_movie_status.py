"""
Lambda function to update a movie's status.

This function:
- Validates the new status value
- Updates the movie status in DynamoDB
- Uses conditional update to ensure movie exists
- Returns the updated movie
"""

import json
import time

from botocore.exceptions import ClientError
from shared.response import success_response, error_response
from shared.dynamodb_client import get_dynamodb_client
from shared.validation import validate_movie_status


def lambda_handler(event, context):
    """
    Update a movie's status.
    
    Args:
        event: API Gateway event containing:
            - pathParameters.movieId: Movie ID
            - body: JSON with 'status' field
        context: Lambda context object
        
    Returns:
        API Gateway response with updated movie or error
    """
    try:
        # Extract movieId from path parameters
        try:
            movie_id = event['pathParameters']['movieId']
        except (KeyError, TypeError):
            return error_response(400, "Missing movieId in path", "ValidationError")
        
        # Parse request body
        try:
            body = json.loads(event.get('body', '{}'))
        except json.JSONDecodeError:
            return error_response(400, "Invalid JSON in request body", "ValidationError")
        
        # Extract and validate new status
        new_status = body.get('status')
        is_valid, error_message = validate_movie_status(new_status)
        if not is_valid:
            return error_response(400, error_message, "ValidationError")
        
        # Get current timestamp
        current_time = int(time.time())
        
        # Update movie in DynamoDB
        try:
            db_client = get_dynamodb_client()
            response = db_client.movies_table.update_item(
                Key={'movieId': movie_id},
                UpdateExpression='SET #status = :status, updatedAt = :updatedAt',
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':status': new_status,
                    ':updatedAt': current_time
                },
                ConditionExpression='attribute_exists(movieId)',
                ReturnValues='ALL_NEW'
            )
            
            updated_movie = response['Attributes']
            return success_response(200, updated_movie)
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                return error_response(404, "Movie not found", "NotFoundError")
            status_code, error_msg = db_client.handle_client_error(e)
            return error_response(status_code, error_msg, "DatabaseError")
        
    except Exception as e:
        print(f"Unexpected error in updateMovieStatus: {str(e)}")
        return error_response(500, "Internal server error", "ServerError")
