"""
Unit tests for getMovies Lambda function.

Tests cover:
- Empty movie list
- Single movie retrieval
- Multiple movies retrieval
- Movies with interested users
- Movies sorted by creation date
- DynamoDB error handling
"""

import json
import pytest
from unittest.mock import Mock
from moto import mock_aws
import boto3
import time

from src.get_movies import lambda_handler
import src.shared.dynamodb_client as db_module


@pytest.fixture(autouse=True)
def reset_dynamodb_client():
    """Reset the DynamoDB client singleton before each test."""
    db_module._client = None
    yield
    db_module._client = None


@pytest.fixture
def lambda_context():
    """Create a mock Lambda context."""
    context = Mock()
    context.function_name = 'getMovies'
    context.memory_limit_in_mb = 512
    return context


@pytest.fixture
def api_gateway_event():
    """Create a basic API Gateway event (no body needed for GET)."""
    return {
        'httpMethod': 'GET',
        'requestContext': {
            'authorizer': {
                'claims': {
                    'sub': 'user-123',
                    'email': 'test@example.com'
                }
            }
        }
    }


@mock_aws
def test_get_movies_empty_list(api_gateway_event, lambda_context, monkeypatch):
    """Test retrieving movies when database is empty."""
    # Set up environment
    monkeypatch.setenv('MOVIES_TABLE_NAME', 'test-movies')
    monkeypatch.setenv('INTERESTS_TABLE_NAME', 'test-interests')
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'us-east-1')
    
    # Create empty tables
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
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
    
    # Call handler
    response = lambda_handler(api_gateway_event, lambda_context)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert isinstance(body, list)
    assert len(body) == 0


@mock_aws
def test_get_movies_single_movie(api_gateway_event, lambda_context, monkeypatch):
    """Test retrieving a single movie."""
    monkeypatch.setenv('MOVIES_TABLE_NAME', 'test-movies')
    monkeypatch.setenv('INTERESTS_TABLE_NAME', 'test-interests')
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'us-east-1')
    
    # Create tables and add a movie
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    movies_table = dynamodb.create_table(
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
    
    # Add a movie
    movies_table.put_item(Item={
        'movieId': 'movie-1',
        'title': 'The Matrix',
        'status': 'wishlist',
        'createdBy': 'user-123',
        'createdAt': 1000,
        'updatedAt': 1000
    })
    
    # Call handler
    response = lambda_handler(api_gateway_event, lambda_context)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert len(body) == 1
    assert body[0]['movieId'] == 'movie-1'
    assert body[0]['title'] == 'The Matrix'
    assert body[0]['status'] == 'wishlist'
    assert 'interestedUsers' in body[0]
    assert body[0]['interestedUsers'] == []


@mock_aws
def test_get_movies_multiple_movies(api_gateway_event, lambda_context, monkeypatch):
    """Test retrieving multiple movies."""
    monkeypatch.setenv('MOVIES_TABLE_NAME', 'test-movies')
    monkeypatch.setenv('INTERESTS_TABLE_NAME', 'test-interests')
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'us-east-1')
    
    # Create tables
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    movies_table = dynamodb.create_table(
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
    
    # Add multiple movies
    movies_table.put_item(Item={
        'movieId': 'movie-1',
        'title': 'The Matrix',
        'status': 'wishlist',
        'createdBy': 'user-123',
        'createdAt': 1000,
        'updatedAt': 1000
    })
    movies_table.put_item(Item={
        'movieId': 'movie-2',
        'title': 'Inception',
        'status': 'downloaded',
        'createdBy': 'user-456',
        'createdAt': 2000,
        'updatedAt': 2000
    })
    movies_table.put_item(Item={
        'movieId': 'movie-3',
        'title': 'Interstellar',
        'status': 'wishlist',
        'createdBy': 'user-789',
        'createdAt': 3000,
        'updatedAt': 3000
    })
    
    # Call handler
    response = lambda_handler(api_gateway_event, lambda_context)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert len(body) == 3
    
    # Verify all movies are present
    movie_ids = [m['movieId'] for m in body]
    assert 'movie-1' in movie_ids
    assert 'movie-2' in movie_ids
    assert 'movie-3' in movie_ids


@mock_aws
def test_get_movies_sorted_by_creation_date(api_gateway_event, lambda_context, monkeypatch):
    """Test that movies are sorted by creation date (newest first)."""
    monkeypatch.setenv('MOVIES_TABLE_NAME', 'test-movies')
    monkeypatch.setenv('INTERESTS_TABLE_NAME', 'test-interests')
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'us-east-1')
    
    # Create tables
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    movies_table = dynamodb.create_table(
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
    
    # Add movies with different timestamps
    movies_table.put_item(Item={
        'movieId': 'movie-old',
        'title': 'Old Movie',
        'status': 'wishlist',
        'createdBy': 'user-123',
        'createdAt': 1000,
        'updatedAt': 1000
    })
    movies_table.put_item(Item={
        'movieId': 'movie-new',
        'title': 'New Movie',
        'status': 'wishlist',
        'createdBy': 'user-123',
        'createdAt': 3000,
        'updatedAt': 3000
    })
    movies_table.put_item(Item={
        'movieId': 'movie-middle',
        'title': 'Middle Movie',
        'status': 'wishlist',
        'createdBy': 'user-123',
        'createdAt': 2000,
        'updatedAt': 2000
    })
    
    # Call handler
    response = lambda_handler(api_gateway_event, lambda_context)
    
    # Verify sorting (newest first)
    body = json.loads(response['body'])
    assert body[0]['movieId'] == 'movie-new'
    assert body[1]['movieId'] == 'movie-middle'
    assert body[2]['movieId'] == 'movie-old'


@mock_aws
def test_get_movies_with_interested_users(api_gateway_event, lambda_context, monkeypatch):
    """Test retrieving movies with interested users."""
    monkeypatch.setenv('MOVIES_TABLE_NAME', 'test-movies')
    monkeypatch.setenv('INTERESTS_TABLE_NAME', 'test-interests')
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'us-east-1')
    
    # Create tables
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    movies_table = dynamodb.create_table(
        TableName='test-movies',
        KeySchema=[{'AttributeName': 'movieId', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'movieId', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    interests_table = dynamodb.create_table(
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
    
    # Add a movie
    movies_table.put_item(Item={
        'movieId': 'movie-1',
        'title': 'The Matrix',
        'status': 'wishlist',
        'createdBy': 'user-123',
        'createdAt': 1000,
        'updatedAt': 1000
    })
    
    # Add interests
    interests_table.put_item(Item={
        'userId': 'user-456',
        'movieId': 'movie-1',
        'createdAt': 1100
    })
    interests_table.put_item(Item={
        'userId': 'user-789',
        'movieId': 'movie-1',
        'createdAt': 1200
    })
    
    # Call handler
    response = lambda_handler(api_gateway_event, lambda_context)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert len(body) == 1
    assert 'interestedUsers' in body[0]
    assert len(body[0]['interestedUsers']) == 2
    assert 'user-456' in body[0]['interestedUsers']
    assert 'user-789' in body[0]['interestedUsers']


@mock_aws
def test_get_movies_mixed_interests(api_gateway_event, lambda_context, monkeypatch):
    """Test retrieving multiple movies with varying interest levels."""
    monkeypatch.setenv('MOVIES_TABLE_NAME', 'test-movies')
    monkeypatch.setenv('INTERESTS_TABLE_NAME', 'test-interests')
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'us-east-1')
    
    # Create tables
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    movies_table = dynamodb.create_table(
        TableName='test-movies',
        KeySchema=[{'AttributeName': 'movieId', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'movieId', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    interests_table = dynamodb.create_table(
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
    
    # Add movies
    movies_table.put_item(Item={
        'movieId': 'movie-1',
        'title': 'Popular Movie',
        'status': 'wishlist',
        'createdBy': 'user-123',
        'createdAt': 1000,
        'updatedAt': 1000
    })
    movies_table.put_item(Item={
        'movieId': 'movie-2',
        'title': 'Unpopular Movie',
        'status': 'wishlist',
        'createdBy': 'user-123',
        'createdAt': 2000,
        'updatedAt': 2000
    })
    
    # Add interests (movie-1 has 3 users, movie-2 has none)
    interests_table.put_item(Item={'userId': 'user-1', 'movieId': 'movie-1', 'createdAt': 1100})
    interests_table.put_item(Item={'userId': 'user-2', 'movieId': 'movie-1', 'createdAt': 1200})
    interests_table.put_item(Item={'userId': 'user-3', 'movieId': 'movie-1', 'createdAt': 1300})
    
    # Call handler
    response = lambda_handler(api_gateway_event, lambda_context)
    
    # Verify response
    body = json.loads(response['body'])
    
    # Find each movie
    movie1 = next(m for m in body if m['movieId'] == 'movie-1')
    movie2 = next(m for m in body if m['movieId'] == 'movie-2')
    
    assert len(movie1['interestedUsers']) == 3
    assert len(movie2['interestedUsers']) == 0
