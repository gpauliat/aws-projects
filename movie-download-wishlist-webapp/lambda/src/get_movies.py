"""
Lambda function to retrieve all movies from the wishlist.

This function:
- Scans the Movies table in DynamoDB
- For each movie, queries the Interests table for interested users
- Resolves user IDs to usernames from Cognito
- Aggregates movie data with interest information
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
    Retrieve all movies from the wishlist.
    
    Args:
        event: API Gateway event (no body required)
        context: Lambda context object
        
    Returns:
        API Gateway response with list of movies or error
    """
    try:
        db_client = get_dynamodb_client()
        
        # Scan Movies table to get all movies
        try:
            movies_response = db_client.movies_table.scan()
            movies = movies_response.get('Items', [])
        except ClientError as e:
            status_code, error_msg = db_client.handle_client_error(e)
            return error_response(status_code, error_msg, "DatabaseError")
        
        # For each movie, get interested users
        enriched_movies = []
        for movie in movies:
            movie_id = movie['movieId']
            
            # Resolve createdBy user ID to username
            movie['createdBy'] = get_username_from_user_id(movie.get('createdBy', ''))
            
            # Query Interests table using GSI to get all users interested in this movie
            try:
                interests_response = db_client.interests_table.query(
                    IndexName='MovieInterestsIndex',
                    KeyConditionExpression='movieId = :movieId',
                    ExpressionAttributeValues={
                        ':movieId': movie_id
                    }
                )
                interests = interests_response.get('Items', [])
                
                # Extract user IDs and resolve to usernames
                interested_users = [get_username_from_user_id(interest['userId']) for interest in interests]
                
                # Add interested users to movie object
                movie['interestedUsers'] = interested_users
                
            except ClientError as e:
                # If we can't get interests, just set empty list
                print(f"Warning: Could not get interests for movie {movie_id}: {str(e)}")
                movie['interestedUsers'] = []
            
            enriched_movies.append(movie)
        
        # Sort movies by createdAt timestamp (newest first)
        enriched_movies.sort(key=lambda x: x.get('createdAt', 0), reverse=True)
        
        # Return movies list (empty array if no movies)
        return success_response(200, enriched_movies)
        
    except Exception as e:
        print(f"Unexpected error in getMovies: {str(e)}")
        return error_response(500, "Internal server error", "ServerError")
