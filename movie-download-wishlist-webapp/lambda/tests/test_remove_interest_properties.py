"""
Property-based tests for removeInterest Lambda function.

**Feature: movie-download-wishlist, Property 11: Interest removal deletes association**
**Validates: Requirements 5.3**

These tests verify that:
- Any user can remove their interest from any movie
- Interest items are deleted from DynamoDB
- Users no longer appear in getInterestedUsers results
- Removal is idempotent (no error if interest doesn't exist)
"""

import json
import os
import pytest
from hypothesis import given, strategies as st, settings
from moto import mock_aws
import boto3

from src.remove_interest import lambda_handler
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
    context.function_name = 'removeInterest'
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


# Property 11: Interest removal deletes association
@mock_aws
@given(
    movie_id=st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789-'),
    user_id=st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789-')
)
@settings(max_examples=20, deadline=3000)
def test_property_interest_removal_deletes_association(movie_id, user_id):
    """
    Property 11: Interest removal deletes association.
    
    For any existing interest, removing it should:
    - Return 204 status code
    - Delete the interest item from DynamoDB
    - User should no longer be associated with the movie
    """
    db_module._client = None
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    setup_dynamodb_tables(dynamodb)
    
    # Create an interest
    interests_table = dynamodb.Table('test-interests')
    interests_table.put_item(Item={
        'userId': user_id,
        'movieId': movie_id,
        'createdAt': 1000
    })
    
    # Verify interest exists
    db_response = interests_table.get_item(Key={
        'userId': user_id,
        'movieId': movie_id
    })
    assert 'Item' in db_response
    
    # Remove interest
    event = create_test_event(movie_id, user_id)
    context = create_lambda_context()
    response = lambda_handler(event, context)
    
    # Verify response
    assert response['statusCode'] == 204
    assert response['body'] == ''
    
    # Verify interest is deleted
    db_response = interests_table.get_item(Key={
        'userId': user_id,
        'movieId': movie_id
    })
    assert 'Item' not in db_response


# Property: Removing non-existent interest is idempotent
@mock_aws
@given(
    movie_id=st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789-'),
    user_id=st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789-')
)
@settings(max_examples=20, deadline=3000)
def test_property_removing_nonexistent_interest_is_idempotent(movie_id, user_id):
    """
    Property: Removing non-existent interest is idempotent.
    
    For any user and movie where no interest exists, removing interest should:
    - Return 204 status code (success)
    - Not cause any errors
    """
    db_module._client = None
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    setup_dynamodb_tables(dynamodb)
    
    # Don't create any interest
    
    # Remove interest (should succeed even though it doesn't exist)
    event = create_test_event(movie_id, user_id)
    context = create_lambda_context()
    response = lambda_handler(event, context)
    
    # Verify response
    assert response['statusCode'] == 204
    assert response['body'] == ''


# Property: Removing interest multiple times is idempotent
@mock_aws
@given(
    movie_id=st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789-'),
    user_id=st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789-')
)
@settings(max_examples=15, deadline=3000)
def test_property_removing_interest_multiple_times_is_idempotent(movie_id, user_id):
    """
    Property: Removing interest multiple times is idempotent.
    
    For any existing interest, removing it multiple times should:
    - Always return 204 status code
    - Not cause any errors
    """
    db_module._client = None
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    setup_dynamodb_tables(dynamodb)
    
    # Create an interest
    interests_table = dynamodb.Table('test-interests')
    interests_table.put_item(Item={
        'userId': user_id,
        'movieId': movie_id,
        'createdAt': 1000
    })
    
    # Remove interest multiple times
    event = create_test_event(movie_id, user_id)
    context = create_lambda_context()
    
    response1 = lambda_handler(event, context)
    assert response1['statusCode'] == 204
    
    response2 = lambda_handler(event, context)
    assert response2['statusCode'] == 204
    
    response3 = lambda_handler(event, context)
    assert response3['statusCode'] == 204
    
    # Verify interest is deleted
    db_response = interests_table.get_item(Key={
        'userId': user_id,
        'movieId': movie_id
    })
    assert 'Item' not in db_response


# Property: Removing one user's interest doesn't affect others
@mock_aws
@given(
    movie_id=st.just('test-movie-123'),
    user_ids=st.lists(
        st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789'),
        min_size=2,
        max_size=5,
        unique=True
    )
)
@settings(max_examples=15, deadline=3000)
def test_property_removing_one_interest_preserves_others(movie_id, user_ids):
    """
    Property: Removing one user's interest doesn't affect other users.
    
    For any movie with multiple interested users, removing one user's
    interest should not affect other users' interests.
    """
    db_module._client = None
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    setup_dynamodb_tables(dynamodb)
    
    # Create interests for all users
    interests_table = dynamodb.Table('test-interests')
    for user_id in user_ids:
        interests_table.put_item(Item={
            'userId': user_id,
            'movieId': movie_id,
            'createdAt': 1000
        })
    
    # Remove first user's interest
    event = create_test_event(movie_id, user_ids[0])
    context = create_lambda_context()
    response = lambda_handler(event, context)
    
    assert response['statusCode'] == 204
    
    # Verify first user's interest is deleted
    db_response = interests_table.get_item(Key={
        'userId': user_ids[0],
        'movieId': movie_id
    })
    assert 'Item' not in db_response
    
    # Verify other users' interests still exist
    for user_id in user_ids[1:]:
        db_response = interests_table.get_item(Key={
            'userId': user_id,
            'movieId': movie_id
        })
        assert 'Item' in db_response


# Property: User can remove interest from one movie without affecting others
@mock_aws
@given(
    user_id=st.just('test-user-123'),
    movie_ids=st.lists(
        st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789'),
        min_size=2,
        max_size=5,
        unique=True
    )
)
@settings(max_examples=15, deadline=3000)
def test_property_removing_interest_from_one_movie_preserves_others(user_id, movie_ids):
    """
    Property: Removing interest from one movie doesn't affect user's other interests.
    
    For any user with interests in multiple movies, removing interest from
    one movie should not affect interests in other movies.
    """
    db_module._client = None
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    setup_dynamodb_tables(dynamodb)
    
    # Create interests for all movies
    interests_table = dynamodb.Table('test-interests')
    for movie_id in movie_ids:
        interests_table.put_item(Item={
            'userId': user_id,
            'movieId': movie_id,
            'createdAt': 1000
        })
    
    # Remove interest from first movie
    event = create_test_event(movie_ids[0], user_id)
    context = create_lambda_context()
    response = lambda_handler(event, context)
    
    assert response['statusCode'] == 204
    
    # Verify interest in first movie is deleted
    db_response = interests_table.get_item(Key={
        'userId': user_id,
        'movieId': movie_ids[0]
    })
    assert 'Item' not in db_response
    
    # Verify interests in other movies still exist
    for movie_id in movie_ids[1:]:
        db_response = interests_table.get_item(Key={
            'userId': user_id,
            'movieId': movie_id
        })
        assert 'Item' in db_response
