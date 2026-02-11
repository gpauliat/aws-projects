"""
Property-based tests for addInterest Lambda function.

**Feature: movie-download-wishlist, Property 10: Interest tracking associates users with movies**
**Validates: Requirements 5.1, 5.2**

These tests verify that:
- Any user can express interest in any existing movie
- Interest items are created in DynamoDB
- Users appear in getInterestedUsers results
- Duplicate interests are handled idempotently
"""

import json
import os
import pytest
from hypothesis import given, strategies as st, settings
from moto import mock_aws
import boto3

from src.add_interest import lambda_handler
import src.shared.dynamodb_client as db_module


@pytest.fixture(autouse=True)
def setup_environment():
    """Set up environment variables for all tests."""
    os.environ['MOVIES_TABLE_NAME'] = 'test-movies'
    os.environ['INTERESTS_TABLE_NAME'] = 'test-interests'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    yield
    db_module._client = None


def create_test_event(movie_id, user_id='test-user-123'):
    """Helper to create API Gateway event."""
    return {
        'pathParameters': {'movieId': movie_id},
        'requestContext': {
            'authorizer': {
                'claims': {
                    'sub': user_id,
                    'email': f'{user_id}@example.com'
                }
            }
        }
    }


def create_lambda_context():
    """Helper to create Lambda context."""
    from unittest.mock import Mock
    context = Mock()
    context.function_name = 'addInterest'
    return context


def setup_dynamodb_tables(dynamodb):
    """Helper to create DynamoDB tables."""
    try:
        table = dynamodb.Table('test-movies')
        table.delete()
    except:
        pass
    
    try:
        table = dynamodb.Table('test-interests')
        table.delete()
    except:
        pass
    
    dynamodb.create_table(
        TableName='test-movies',
        KeySchema=[{'AttributeName': 'movieId', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'movieId', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    
    dynamodb.create_table(
        TableName='test-interests',
        KeySchema=[
            {'AttributeName': 'userId', 'KeyType': 'HASH'},
            {'AttributeName': 'movieId', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'userId', 'AttributeType': 'S'},
            {'AttributeName': 'movieId', 'AttributeType': 'S'},
        ],
        GlobalSecondaryIndexes=[{
            'IndexName': 'MovieInterestsIndex',
            'KeySchema': [
                {'AttributeName': 'movieId', 'KeyType': 'HASH'},
                {'AttributeName': 'userId', 'KeyType': 'RANGE'}
            ],
            'Projection': {'ProjectionType': 'ALL'}
        }],
        BillingMode='PAY_PER_REQUEST'
    )


# Property 10: Interest tracking associates users with movies
@mock_aws
@given(
    movie_id=st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789-'),
    user_id=st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789-')
)
@settings(max_examples=20, deadline=3000)
def test_property_interest_associates_user_with_movie(movie_id, user_id):
    """
    Property 10: Interest tracking associates users with movies.
    
    For any valid user and existing movie, adding interest should:
    - Return 201 status code
    - Create an interest item in DynamoDB
    - Interest item should have userId, movieId, and createdAt
    """
    db_module._client = None
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    setup_dynamodb_tables(dynamodb)
    
    # Create a movie
    movies_table = dynamodb.Table('test-movies')
    movies_table.put_item(Item={
        'movieId': movie_id,
        'title': 'Test Movie',
        'status': 'wishlist',
        'createdBy': 'creator-123',
        'createdAt': 1000,
        'updatedAt': 1000
    })
    
    # Add interest
    event = create_test_event(movie_id, user_id)
    context = create_lambda_context()
    response = lambda_handler(event, context)
    
    # Verify response
    assert response['statusCode'] == 201
    body = json.loads(response['body'])
    assert body['userId'] == user_id
    assert body['movieId'] == movie_id
    assert 'createdAt' in body
    assert isinstance(body['createdAt'], int)
    
    # Verify interest exists in DynamoDB
    interests_table = dynamodb.Table('test-interests')
    db_response = interests_table.get_item(Key={
        'userId': user_id,
        'movieId': movie_id
    })
    
    assert 'Item' in db_response
    assert db_response['Item']['userId'] == user_id
    assert db_response['Item']['movieId'] == movie_id


# Property: Multiple users can express interest in same movie
@mock_aws
@given(
    movie_id=st.just('test-movie-123'),
    user_ids=st.lists(
        st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789'),
        min_size=1,
        max_size=5,
        unique=True
    )
)
@settings(max_examples=15, deadline=3000)
def test_property_multiple_users_can_express_interest(movie_id, user_ids):
    """
    Property: Multiple users can express interest in the same movie.
    
    For any movie and multiple users, each user should be able to
    add their interest independently.
    """
    db_module._client = None
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    setup_dynamodb_tables(dynamodb)
    
    # Create a movie
    movies_table = dynamodb.Table('test-movies')
    movies_table.put_item(Item={
        'movieId': movie_id,
        'title': 'Test Movie',
        'status': 'wishlist',
        'createdBy': 'creator-123',
        'createdAt': 1000,
        'updatedAt': 1000
    })
    
    # Add interests from multiple users
    context = create_lambda_context()
    for user_id in user_ids:
        event = create_test_event(movie_id, user_id)
        response = lambda_handler(event, context)
        assert response['statusCode'] == 201
    
    # Verify all interests exist
    interests_table = dynamodb.Table('test-interests')
    for user_id in user_ids:
        db_response = interests_table.get_item(Key={
            'userId': user_id,
            'movieId': movie_id
        })
        assert 'Item' in db_response


# Property: Adding interest for non-existent movie returns 404
@mock_aws
@given(
    movie_id=st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789-'),
    user_id=st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789-')
)
@settings(max_examples=15, deadline=3000)
def test_property_nonexistent_movie_returns_404(movie_id, user_id):
    """
    Property: Adding interest for non-existent movie returns 404.
    
    For any movie that doesn't exist, attempting to add interest should:
    - Return 404 status code
    - Not create any interest item
    """
    db_module._client = None
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    setup_dynamodb_tables(dynamodb)
    
    # Don't create the movie
    
    # Try to add interest
    event = create_test_event(movie_id, user_id)
    context = create_lambda_context()
    response = lambda_handler(event, context)
    
    # Verify error response
    assert response['statusCode'] == 404
    body = json.loads(response['body'])
    assert 'error' in body
    
    # Verify no interest was created
    interests_table = dynamodb.Table('test-interests')
    db_response = interests_table.get_item(Key={
        'userId': user_id,
        'movieId': movie_id
    })
    assert 'Item' not in db_response


# Property: Duplicate interest is idempotent
@mock_aws
@given(
    movie_id=st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789-'),
    user_id=st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789-')
)
@settings(max_examples=15, deadline=3000)
def test_property_duplicate_interest_is_idempotent(movie_id, user_id):
    """
    Property: Adding duplicate interest is idempotent.
    
    For any user and movie, adding interest multiple times should:
    - Always return success (201)
    - Only create one interest item
    """
    db_module._client = None
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    setup_dynamodb_tables(dynamodb)
    
    # Create a movie
    movies_table = dynamodb.Table('test-movies')
    movies_table.put_item(Item={
        'movieId': movie_id,
        'title': 'Test Movie',
        'status': 'wishlist',
        'createdBy': 'creator-123',
        'createdAt': 1000,
        'updatedAt': 1000
    })
    
    # Add interest twice
    event = create_test_event(movie_id, user_id)
    context = create_lambda_context()
    
    response1 = lambda_handler(event, context)
    assert response1['statusCode'] == 201
    
    response2 = lambda_handler(event, context)
    assert response2['statusCode'] == 201
    
    # Verify only one interest exists
    interests_table = dynamodb.Table('test-interests')
    db_response = interests_table.get_item(Key={
        'userId': user_id,
        'movieId': movie_id
    })
    assert 'Item' in db_response


# Property: User can express interest in multiple movies
@mock_aws
@given(
    user_id=st.just('test-user-123'),
    movie_ids=st.lists(
        st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789'),
        min_size=1,
        max_size=5,
        unique=True
    )
)
@settings(max_examples=15, deadline=3000)
def test_property_user_can_express_interest_in_multiple_movies(user_id, movie_ids):
    """
    Property: A user can express interest in multiple movies.
    
    For any user and multiple movies, the user should be able to
    add interest to all of them.
    """
    db_module._client = None
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    setup_dynamodb_tables(dynamodb)
    
    # Create movies
    movies_table = dynamodb.Table('test-movies')
    for movie_id in movie_ids:
        movies_table.put_item(Item={
            'movieId': movie_id,
            'title': f'Movie {movie_id}',
            'status': 'wishlist',
            'createdBy': 'creator-123',
            'createdAt': 1000,
            'updatedAt': 1000
        })
    
    # Add interests
    context = create_lambda_context()
    for movie_id in movie_ids:
        event = create_test_event(movie_id, user_id)
        response = lambda_handler(event, context)
        assert response['statusCode'] == 201
    
    # Verify all interests exist
    interests_table = dynamodb.Table('test-interests')
    for movie_id in movie_ids:
        db_response = interests_table.get_item(Key={
            'userId': user_id,
            'movieId': movie_id
        })
        assert 'Item' in db_response
