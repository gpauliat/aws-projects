"""
Lambda function to get all users interested in a movie.
"""

import os
import boto3
from botocore.exceptions import ClientError
from shared.response import success_response, error_response
from shared.dynamodb_client import get_dynamodb_client


def lambda_handler(event, context):
    """
    Get all users interested in a movie.
    
    Args:
        event: API Gateway event with pathParameters.movieId
        context: Lambda context object
        
    Returns:
        200 OK with list of users
    """
    try:
        # Extract movieId
        try:
            movie_id = event['pathParameters']['movieId']
        except (KeyError, TypeError):
            return error_response(400, "Missing movieId in path", "ValidationError")
        
        db_client = get_dynamodb_client()
        
        # Query interests using GSI
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
        
        # Get user details from Cognito
        user_pool_id = os.environ.get('USER_POOL_ID')
        users = []
        
        if user_pool_id:
            # Lambda automatically provides AWS_REGION environment variable
            region = os.environ.get('AWS_REGION', 'eu-west-3')
            cognito = boto3.client('cognito-idp', region_name=region)
            
            for interest in interests:
                user_id = interest['userId']
                try:
                    user_response = cognito.admin_get_user(
                        UserPoolId=user_pool_id,
                        Username=user_id
                    )
                    
                    # Extract email from attributes
                    email = None
                    for attr in user_response.get('UserAttributes', []):
                        if attr['Name'] == 'email':
                            email = attr['Value']
                            break
                    
                    users.append({
                        'userId': user_id,
                        'username': user_response.get('Username'),
                        'email': email
                    })
                except ClientError as e:
                    # User might have been deleted, skip
                    print(f"Could not get user {user_id}: {str(e)}")
                    users.append({
                        'userId': user_id,
                        'username': None,
                        'email': None
                    })
        else:
            # No Cognito integration, just return user IDs
            users = [{'userId': interest['userId']} for interest in interests]
        
        return success_response(200, users)
        
    except Exception as e:
        print(f"Unexpected error in getInterestedUsers: {str(e)}")
        return error_response(500, "Internal server error", "ServerError")
