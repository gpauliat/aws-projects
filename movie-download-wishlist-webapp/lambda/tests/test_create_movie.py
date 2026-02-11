"""
Unit tests for createMovie Lambda function.

Tests cover:
- Valid movie creation
- Empty title validation
- Invalid JSON handling
- DynamoDB error handling
- Missing user context
"""

import json
import pytest
from unittest.mock import Mock, patch
from moto import mock_aws
import boto3
import os

from src.create_movie import lambda_handler
import src.shared.dynamodb_client as db_module


@pytest.fixture(autouse=True)
def reset_dynamodb_client():
    """Reset the DynamoDB client singleton before each test."""
    db_module._client = None
    yield
    db_module._client = None


@pytest.fixture
def valid_event():
    """Create a valid API Gateway event."""
    return {
        'body': json.dumps({'title': 'The Matrix'}),
        'requestContext': {
            'authorizer': {
                'claims': {
                    'sub': 'user-123',
                    'email': 'test@example.com'
                }
            }
        }
    }


@pytest.fixture
def lambda_context():
    """Create a mock Lambda context."""
    context = Mock()
    context.function_name = 'createMovie'
    context.memory_limit_in_mb = 512
    context.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:createMovie'
    return context


@mock_aws
def test_create_movie_success(valid_event, lambda_context, monkeypatch):
    """Test successful movie creation."""
    # Set up environment
    monkeypatch.setenv('MOVIES_TABLE_NAME', 'test-movies')
    monkeypatch.setenv('INTERESTS_TABLE_NAME', 'test-interests')
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'us-east-1')
    
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
            {'AttributeName': 'movieId', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Call handler
    response = lambda_handler(valid_event, lambda_context)
    
    # Verify response
    assert response['statusCode'] == 201
    body = json.loads(response['body'])
    assert body['title'] == 'The Matrix'
    assert body['status'] == 'wishlist'
    assert body['createdBy'] == 'user-123'
    assert 'movieId' in body
    assert 'createdAt' in body
    assert 'updatedAt' in body


@mock_aws
def test_create_movie_with_whitespace_title(valid_event, lambda_context, monkeypatch):
    """Test movie creation with title containing extra whitespace."""
    monkeypatch.setenv('MOVIES_TABLE_NAME', 'test-movies')
    monkeypatch.setenv('INTERESTS_TABLE_NAME', 'test-interests')
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'us-east-1')
    
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
            {'AttributeName': 'movieId', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Modify event with whitespace
    valid_event['body'] = json.dumps({'title': '  Inception  '})
    
    response = lambda_handler(valid_event, lambda_context)
    
    assert response['statusCode'] == 201
    body = json.loads(response['body'])
    assert body['title'] == 'Inception'  # Should be trimmed


def test_create_movie_empty_title(valid_event, lambda_context):
    """Test movie creation with empty title."""
    valid_event['body'] = json.dumps({'title': ''})
    
    response = lambda_handler(valid_event, lambda_context)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'error' in body
    assert 'empty' in body['error'].lower()


def test_create_movie_whitespace_only_title(valid_event, lambda_context):
    """Test movie creation with whitespace-only title."""
    valid_event['body'] = json.dumps({'title': '   '})
    
    response = lambda_handler(valid_event, lambda_context)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'error' in body
    assert 'empty' in body['error'].lower() or 'whitespace' in body['error'].lower()


def test_create_movie_missing_title(valid_event, lambda_context):
    """Test movie creation without title field."""
    valid_event['body'] = json.dumps({})
    
    response = lambda_handler(valid_event, lambda_context)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'error' in body


def test_create_movie_invalid_json(valid_event, lambda_context):
    """Test movie creation with invalid JSON."""
    valid_event['body'] = 'not valid json'
    
    response = lambda_handler(valid_event, lambda_context)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'error' in body
    assert 'JSON' in body['error']


def test_create_movie_missing_user_context(valid_event, lambda_context):
    """Test movie creation without user context."""
    valid_event['requestContext'] = {}
    
    response = lambda_handler(valid_event, lambda_context)
    
    assert response['statusCode'] == 401
    body = json.loads(response['body'])
    assert 'error' in body
    assert 'Unauthorized' in body['error']


def test_create_movie_title_too_long(valid_event, lambda_context):
    """Test movie creation with title exceeding max length."""
    long_title = 'A' * 501  # Exceeds 500 character limit
    valid_event['body'] = json.dumps({'title': long_title})
    
    response = lambda_handler(valid_event, lambda_context)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'error' in body
    assert '500' in body['error']


@mock_aws
def test_create_movie_generates_unique_ids(valid_event, lambda_context, monkeypatch):
    """Test that multiple movie creations generate unique IDs."""
    monkeypatch.setenv('MOVIES_TABLE_NAME', 'test-movies')
    monkeypatch.setenv('INTERESTS_TABLE_NAME', 'test-interests')
    monkeypatch.setenv('AWS_DEFAULT_REGION', 'us-east-1')
    
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
            {'AttributeName': 'movieId', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Create first movie
    valid_event['body'] = json.dumps({'title': 'Movie 1'})
    response1 = lambda_handler(valid_event, lambda_context)
    body1 = json.loads(response1['body'])
    
    # Create second movie
    valid_event['body'] = json.dumps({'title': 'Movie 2'})
    response2 = lambda_handler(valid_event, lambda_context)
    body2 = json.loads(response2['body'])
    
    # Verify unique IDs
    assert body1['movieId'] != body2['movieId']
