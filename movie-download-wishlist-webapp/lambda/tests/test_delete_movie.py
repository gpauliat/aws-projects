"""
Unit tests for deleteMovie Lambda function.

Requirements: 6.4

These tests verify that:
- Movies can be deleted successfully
- Associated interests are deleted atomically
- Non-existent movies return 404
- Transactions maintain atomicity
"""

import json
import os
import pytest
from moto import mock_aws
import boto3

from src.delete_movie import lambda_handler
import src.shared.dynamodb_client as db_module


@pytest.fixture(autouse=True)
def setup_environment():
    """Set up environment variables for all tests."""
    os.environ['MOVIES_TABLE_NAME'] = 'test-movies'
    os.environ['INTERESTS_TABLE_NAME'] = 'test-interests'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    yield
    db_module._client = None


def create_test_event(movie_id):
    """Helper to create API Gateway event."""
    return {
        'pathParameters': {'movieId': movie_id},
        'requestContext': {
            'authorizer': {
                'claims': {
                    'sub': 'test-user-123',
                    'email': 'test@example.com'
                }
            }
        }
    }


def create_lambda_context():
    """Helper to create Lambda context."""
    from unittest.mock import Mock
    context = Mock()
    context.function_name = 'deleteMovie'
    return context


def setup_dynamodb_tables(dynamodb):
    """Helper to create DynamoDB tables."""
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


@mock_aws
def test_delete_movie_with_no_interests():
    """Test successful deletion of movie with no interests."""
    db_module._client = None
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    setup_dynamodb_tables(dynamodb)
    
    # Create a movie
    movies_table = dynamodb.Table('test-movies')
    movies_table.put_item(Item={
        'movieId': 'movie-123',
        'title': 'Test Movie',
        'status': 'wishlist',
        'createdBy': 'user-123',
        'createdAt': 1000,
        'updatedAt': 1000
    })
    
    # Delete the movie
    event = create_test_event('movie-123')
    context = create_lambda_context()
    response = lambda_handler(event, context)
    
    # Verify response
    assert response['statusCode'] == 204
    assert response['body'] == ''
    
    # Verify movie is deleted
    db_response = movies_table.get_item(Key={'movieId': 'movie-123'})
    assert 'Item' not in db_response


@mock_aws
def test_delete_movie_with_multiple_interests():
    """Test successful deletion of movie with multiple interests."""
    db_module._client = None
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    setup_dynamodb_tables(dynamodb)
    
    # Create a movie
    movies_table = dynamodb.Table('test-movies')
    movies_table.put_item(Item={
        'movieId': 'movie-123',
        'title': 'Test Movie',
        'status': 'wishlist',
        'createdBy': 'user-123',
        'createdAt': 1000,
        'updatedAt': 1000
    })
    
    # Create multiple interests
    interests_table = dynamodb.Table('test-interests')
    interests_table.put_item(Item={
        'userId': 'user-1',
        'movieId': 'movie-123',
        'createdAt': 1100
    })
    interests_table.put_item(Item={
        'userId': 'user-2',
        'movieId': 'movie-123',
        'createdAt': 1100
    })
    interests_table.put_item(Item={
        'userId': 'user-3',
        'movieId': 'movie-123',
        'createdAt': 1100
    })
    
    # Delete the movie
    event = create_test_event('movie-123')
    context = create_lambda_context()
    response = lambda_handler(event, context)
    
    # Verify response
    assert response['statusCode'] == 204
    
    # Verify movie is deleted
    db_response = movies_table.get_item(Key={'movieId': 'movie-123'})
    assert 'Item' not in db_response
    
    # Verify all interests are deleted
    for user_id in ['user-1', 'user-2', 'user-3']:
        db_response = interests_table.get_item(Key={
            'userId': user_id,
            'movieId': 'movie-123'
        })
        assert 'Item' not in db_response


@mock_aws
def test_delete_nonexistent_movie():
    """Test 404 response for non-existent movie."""
    db_module._client = None
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    setup_dynamodb_tables(dynamodb)
    
    # Try to delete non-existent movie
    event = create_test_event('nonexistent-movie')
    context = create_lambda_context()
    response = lambda_handler(event, context)
    
    # Verify error response
    assert response['statusCode'] == 404
    body = json.loads(response['body'])
    assert 'error' in body
    assert 'not found' in body['error'].lower()


@mock_aws
def test_delete_movie_missing_movie_id():
    """Test 400 response when movieId is missing."""
    db_module._client = None
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    setup_dynamodb_tables(dynamodb)
    
    # Create event without movieId
    event = {
        'pathParameters': {},
        'requestContext': {
            'authorizer': {
                'claims': {'sub': 'test-user-123'}
            }
        }
    }
    context = create_lambda_context()
    response = lambda_handler(event, context)
    
    # Verify error response
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'error' in body


@mock_aws
def test_delete_movie_preserves_other_interests():
    """Test that deleting a movie doesn't affect interests for other movies."""
    db_module._client = None
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    setup_dynamodb_tables(dynamodb)
    
    # Create two movies
    movies_table = dynamodb.Table('test-movies')
    movies_table.put_item(Item={
        'movieId': 'movie-1',
        'title': 'Movie 1',
        'status': 'wishlist',
        'createdBy': 'user-123',
        'createdAt': 1000,
        'updatedAt': 1000
    })
    movies_table.put_item(Item={
        'movieId': 'movie-2',
        'title': 'Movie 2',
        'status': 'wishlist',
        'createdBy': 'user-123',
        'createdAt': 1000,
        'updatedAt': 1000
    })
    
    # Create interests for both movies
    interests_table = dynamodb.Table('test-interests')
    interests_table.put_item(Item={
        'userId': 'user-1',
        'movieId': 'movie-1',
        'createdAt': 1100
    })
    interests_table.put_item(Item={
        'userId': 'user-1',
        'movieId': 'movie-2',
        'createdAt': 1100
    })
    
    # Delete movie-1
    event = create_test_event('movie-1')
    context = create_lambda_context()
    response = lambda_handler(event, context)
    
    assert response['statusCode'] == 204
    
    # Verify movie-1 interest is deleted
    db_response = interests_table.get_item(Key={
        'userId': 'user-1',
        'movieId': 'movie-1'
    })
    assert 'Item' not in db_response
    
    # Verify movie-2 interest still exists
    db_response = interests_table.get_item(Key={
        'userId': 'user-1',
        'movieId': 'movie-2'
    })
    assert 'Item' in db_response
    
    # Verify movie-2 still exists
    db_response = movies_table.get_item(Key={'movieId': 'movie-2'})
    assert 'Item' in db_response
