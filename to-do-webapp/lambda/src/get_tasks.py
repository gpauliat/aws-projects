"""
Lambda function to retrieve all the tasks of a user.

This function:
- Scans the Tasks table in DynamoDB
- Resolves user IDs to usernames from Cognito
- Returns list sorted by creation date
"""

import os
import boto3
from botocore.exceptions import ClientError
from shared.response import success_response, error_response
from shared.dynamodb_client import get_dynamodb_client


# Initialize Cognito client
cognito_client = boto3.client('cognito-idp')
USER_POOL_ID = os.environ.get('USER_POOL_ID')


def get_username_from_user_id(user_id):
    """
    Get username from Cognito user ID (sub).
    
    Args:
        user_id: Cognito user sub (UUID)
        
    Returns:
        Username string or user_id if not found
    """
    try:
        # Use ListUsers with filter on sub attribute to find the username
        response = cognito_client.list_users(
            UserPoolId=USER_POOL_ID,
            Filter=f'sub = "{user_id}"',
            Limit=1
        )
        
        users = response.get('Users', [])
        if users and len(users) > 0:
            return users[0].get('Username', user_id)
        else:
            print(f"Warning: No user found with sub {user_id}")
            return user_id
    except Exception as e:
        print(f"Warning: Could not get username for {user_id}: {str(e)}")
        return user_id  # Return user_id as fallback


def lambda_handler(event, context):
    """
    Retrieve all the user's tasks from the To Do list
    
    Args:
        event: API Gateway event (no body required)
        context: Lambda context object
        
    Returns:
        API Gateway response with list of tasks or error
    """
    try:
        # Extract userId from Cognito context
        try:
            user_claims = event['requestContext']['authorizer']['claims']
            user_id = user_claims['sub']
        except (KeyError, TypeError):
            return error_response(401, "Unauthorized - missing user context", "AuthError")
        
        db_client = get_dynamodb_client()
        
        # Query Tasks table by userId using GSI
        try:
            tasks_response = db_client.tasks_table.query(
                IndexName='UserIdIndex',
                KeyConditionExpression='createdBy = :userId',
                ExpressionAttributeValues={
                    ':userId': user_id
                }
            )
            tasks = tasks_response.get('Items', [])
        except ClientError as e:
            status_code, error_msg = db_client.handle_client_error(e)
            return error_response(status_code, error_msg, "DatabaseError")
        

        # Sort tasks by createdAt timestamp (newest first)
        tasks.sort(key=lambda x: x.get('createdAt', 0), reverse=True)
        
        # Return tasks list (empty array if no tasks)
        return success_response(200, tasks)
        
    except Exception as e:
        print(f"Unexpected error in getTasks: {str(e)}")
        return error_response(500, "Internal server error", "ServerError")
