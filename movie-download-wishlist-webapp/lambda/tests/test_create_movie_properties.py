"""
Property-based tests for createMovie Lambda function.

**Feature: movie-download-wishlist, Property 7: Movie creation adds to list**
**Validates: Requirements 3.1, 3.3, 3.4**

**Feature: movie-download-wishlist, Property 8: Empty titles are rejected**
**Validates: Requirements 3.2**

These tests verify that:
- Any valid movie title results in a movie being created in DynamoDB
- All created movies appear with correct attributes
- Any empty/whitespace-only string is rejected
"""

import json
import os
import pytest
from hypothesis import given, strategies as st, settings
from moto import mock_aws
import boto3

from src.create_movie import lambda_handler
import src.shared.dynamodb_client as db_module


@pytest.fixture(autouse=True)
def setup_environment():
    """Set up environment variables for all tests."""
    os.environ['MOVIES_TABLE_NAME'] = 'test-movies'
    os.environ['INTERESTS_TABLE_NAME'] = 'test-interests'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    yield
    # Clean up
    db_module._client = None


def create_test_event(title, user_id='test-user-123'):
    """Helper to create API Gateway event."""
    return {
        'body': json.dumps({'title': title}),
        'requestContext': {
            'authorizer': {
                'claims': {
                    'sub': user_id,
                    'email': 'test@example.com'
                }
            }
        }
    }


def create_lambda_context():
    """Helper to create Lambda context."""
    from unittest.mock import Mock
    context = Mock()
    context.function_name = 'createMovie'
    return context


# Property 7: Movie creation adds to list
@mock_aws
@given(
    title=st.text(min_size=1, max_size=500).filter(lambda x: x.strip() != '')
)
@settings(max_examples=100, deadline=None)
def test_property_valid_titles_create_movies(title):
    """
    Property 7: Movie creation adds to list.
    
    For any valid (non-empty) movie title, calling createMovie should:
    - Return 201 status code
    - Create a movie in DynamoDB with correct attributes
    - Movie should have wishlist status
    - Movie should have a unique movieId
    """
    # Reset client for each test
    db_module._client = None
    
    # Create DynamoDB tables
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    
    # Check if table exists, create if not
    try:
        table = dynamodb.Table('test-movies')
        table.load()
    except:
        dynamodb.create_table(
            TableName='test-movies',
            KeySchema=[{'AttributeName': 'movieId', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'movieId', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
    
    try:
        table = dynamodb.Table('test-interests')
        table.load()
    except:
        dynamodb.create_table(
            TableName='test-interests',
            KeySchema=[
                {'AttributeName': 'userId', 'KeyType': 'HASH'},
                {'AttributeName': 'movieId', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'userId', 'AttributeType': 'S'},
                {'AttributeName': 'movieId', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
    
    # Create event and call handler
    event = create_test_event(title)
    context = create_lambda_context()
    
    response = lambda_handler(event, context)
    
    # Verify response
    assert response['statusCode'] == 201, f"Expected 201, got {response['statusCode']}"
    
    body = json.loads(response['body'])
    
    # Verify movie attributes
    assert 'movieId' in body
    assert body['title'] == title.strip()  # Title should be trimmed
    assert body['status'] == 'wishlist'
    assert body['createdBy'] == 'test-user-123'
    assert 'createdAt' in body
    assert 'updatedAt' in body
    assert isinstance(body['createdAt'], int)
    assert isinstance(body['updatedAt'], int)
    
    # Verify movie exists in DynamoDB
    table = dynamodb.Table('test-movies')
    db_response = table.get_item(Key={'movieId': body['movieId']})
    
    assert 'Item' in db_response
    db_item = db_response['Item']
    assert db_item['title'] == title.strip()
    assert db_item['status'] == 'wishlist'


# Property 8: Empty titles are rejected
@given(
    whitespace_string=st.one_of(
        st.just(''),
        st.text(max_size=50).filter(lambda x: x.strip() == ''),
        st.from_regex(r'^\s+$', fullmatch=True)
    )
)
@settings(max_examples=100, deadline=None)
def test_property_empty_titles_rejected(whitespace_string):
    """
    Property 8: Empty titles are rejected.
    
    For any string composed entirely of whitespace or empty string,
    attempting to create a movie should:
    - Return 400 status code
    - Return a validation error message
    - Not create any movie in DynamoDB
    """
    # Reset client
    db_module._client = None
    
    # Create event and call handler
    event = create_test_event(whitespace_string)
    context = create_lambda_context()
    
    response = lambda_handler(event, context)
    
    # Verify error response
    assert response['statusCode'] == 400, f"Expected 400 for empty title, got {response['statusCode']}"
    
    body = json.loads(response['body'])
    assert 'error' in body
    assert isinstance(body['error'], str)
    assert len(body['error']) > 0


# Additional property: Multiple movies have unique IDs
@mock_aws
@given(
    titles=st.lists(
        st.text(min_size=1, max_size=100).filter(lambda x: x.strip() != ''),
        min_size=2,
        max_size=10
    )
)
@settings(max_examples=50, deadline=None)
def test_property_unique_movie_ids(titles):
    """
    Property: Each created movie has a unique movieId.
    
    For any list of valid movie titles, creating multiple movies should:
    - Generate unique movieId for each movie
    - All movies should be retrievable from DynamoDB
    """
    # Reset client
    db_module._client = None
    
    # Create DynamoDB tables
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    
    try:
        table = dynamodb.Table('test-movies')
        table.load()
    except:
        dynamodb.create_table(
            TableName='test-movies',
            KeySchema=[{'AttributeName': 'movieId', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'movieId', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
    
    try:
        table = dynamodb.Table('test-interests')
        table.load()
    except:
        dynamodb.create_table(
            TableName='test-interests',
            KeySchema=[
                {'AttributeName': 'userId', 'KeyType': 'HASH'},
                {'AttributeName': 'movieId', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'userId', 'AttributeType': 'S'},
                {'AttributeName': 'movieId', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
    
    # Create multiple movies
    movie_ids = []
    context = create_lambda_context()
    
    for title in titles:
        event = create_test_event(title)
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 201
        body = json.loads(response['body'])
        movie_ids.append(body['movieId'])
    
    # Verify all IDs are unique
    assert len(movie_ids) == len(set(movie_ids)), "Movie IDs should be unique"
    
    # Verify all movies exist in DynamoDB
    table = dynamodb.Table('test-movies')
    for movie_id in movie_ids:
        db_response = table.get_item(Key={'movieId': movie_id})
        assert 'Item' in db_response


# Property: Title length validation
@given(
    long_title=st.text(min_size=501, max_size=1000)
)
@settings(max_examples=50, deadline=None)
def test_property_long_titles_rejected(long_title):
    """
    Property: Titles exceeding 500 characters are rejected.
    
    For any title longer than 500 characters, attempting to create a movie should:
    - Return 400 status code
    - Return a validation error mentioning the length limit
    """
    # Reset client
    db_module._client = None
    
    # Create event and call handler
    event = create_test_event(long_title)
    context = create_lambda_context()
    
    response = lambda_handler(event, context)
    
    # Verify error response
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'error' in body
    assert '500' in body['error']  # Error message should mention the limit
