"""
Unit tests for getInterestedUsers Lambda function.

Requirements: 5.2, 5.4

These tests verify that:
- Empty interests list returns empty array
- Multiple interests return all users
- Cognito user lookup works for each userId
- Deleted Cognito users are handled gracefully
"""

import json
import os
import pytest
from moto import mock_aws
import boto3
from unittest.mock import patch, MagicMock

from src.get_interested_users import lambda_handler
import src.shared.dynamodb_client as db_module


@pytest.fixture(autouse=True)
def setup_environment():
    """Set up environment variables for all tests."""
    os.environ['MOVIES_TABLE_NAME'] = 'test-movies'
    os.environ['INTERESTS_TABLE_NAME'] = 'test-interests'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    os.environ['USER_POOL_ID'] = 'us-east-1_testpool'
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
    context.function_name = 'getInterestedUsers'
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
def test_empty_interests_returns_empty_array():
    """Test that a movie with no interests returns an empty array."""
    db_module._client = None
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    setup_dynamodb_tables(dynamodb)
    
    # Don't create any interests
    
    # Call handler
    event = create_test_event('movie-123')
    context = create_lambda_context()
    response = lambda_handler(event, context)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert isinstance(body, list)
    assert len(body) == 0


@mock_aws
@patch('boto3.client')
def test_multiple_interests_return_all_users(mock_boto_client):
    """Test that multiple interests return all users with Cognito details."""
    db_module._client = None
    
    # Mock Cognito client
    mock_cognito = MagicMock()
    mock_boto_client.return_value = mock_cognito
    
    # Set up Cognito responses
    def admin_get_user_side_effect(UserPoolId, Username):
        user_data = {
            'user-1': {
                'Username': 'user-1',
                'UserAttributes': [
                    {'Name': 'email', 'Value': 'user1@example.com'}
                ]
            },
            'user-2': {
                'Username': 'user-2',
                'UserAttributes': [
                    {'Name': 'email', 'Value': 'user2@example.com'}
                ]
            },
            'user-3': {
                'Username': 'user-3',
                'UserAttributes': [
                    {'Name': 'email', 'Value': 'user3@example.com'}
                ]
            }
        }
        return user_data.get(Username, {})
    
    mock_cognito.admin_get_user.side_effect = admin_get_user_side_effect
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    setup_dynamodb_tables(dynamodb)
    
    # Create interests
    interests_table = dynamodb.Table('test-interests')
    interests_table.put_item(Item={
        'userId': 'user-1',
        'movieId': 'movie-123',
        'createdAt': 1000
    })
    interests_table.put_item(Item={
        'userId': 'user-2',
        'movieId': 'movie-123',
        'createdAt': 1001
    })
    interests_table.put_item(Item={
        'userId': 'user-3',
        'movieId': 'movie-123',
        'createdAt': 1002
    })
    
    # Call handler
    event = create_test_event('movie-123')
    context = create_lambda_context()
    response = lambda_handler(event, context)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert len(body) == 3
    
    # Verify all users are present with correct details
    user_ids = {user['userId'] for user in body}
    assert user_ids == {'user-1', 'user-2', 'user-3'}
    
    # Verify user details
    for user in body:
        assert 'userId' in user
        assert 'username' in user
        assert 'email' in user
        if user['userId'] == 'user-1':
            assert user['email'] == 'user1@example.com'
        elif user['userId'] == 'user-2':
            assert user['email'] == 'user2@example.com'
        elif user['userId'] == 'user-3':
            assert user['email'] == 'user3@example.com'


@mock_aws
@patch('boto3.client')
def test_cognito_user_lookup(mock_boto_client):
    """Test that Cognito user lookup is called for each userId."""
    db_module._client = None
    
    # Mock Cognito client
    mock_cognito = MagicMock()
    mock_boto_client.return_value = mock_cognito
    
    mock_cognito.admin_get_user.return_value = {
        'Username': 'user-1',
        'UserAttributes': [
            {'Name': 'email', 'Value': 'user1@example.com'}
        ]
    }
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    setup_dynamodb_tables(dynamodb)
    
    # Create interest
    interests_table = dynamodb.Table('test-interests')
    interests_table.put_item(Item={
        'userId': 'user-1',
        'movieId': 'movie-123',
        'createdAt': 1000
    })
    
    # Call handler
    event = create_test_event('movie-123')
    context = create_lambda_context()
    response = lambda_handler(event, context)
    
    # Verify Cognito was called
    assert response['statusCode'] == 200
    mock_cognito.admin_get_user.assert_called_once_with(
        UserPoolId='us-east-1_testpool',
        Username='user-1'
    )


@mock_aws
@patch('boto3.client')
def test_deleted_cognito_user_handled_gracefully(mock_boto_client):
    """Test that deleted Cognito users are handled gracefully."""
    db_module._client = None
    
    # Mock Cognito client
    mock_cognito = MagicMock()
    mock_boto_client.return_value = mock_cognito
    
    # Simulate user not found in Cognito
    from botocore.exceptions import ClientError
    mock_cognito.admin_get_user.side_effect = ClientError(
        {'Error': {'Code': 'UserNotFoundException', 'Message': 'User not found'}},
        'AdminGetUser'
    )
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    setup_dynamodb_tables(dynamodb)
    
    # Create interest for deleted user
    interests_table = dynamodb.Table('test-interests')
    interests_table.put_item(Item={
        'userId': 'deleted-user',
        'movieId': 'movie-123',
        'createdAt': 1000
    })
    
    # Call handler
    event = create_test_event('movie-123')
    context = create_lambda_context()
    response = lambda_handler(event, context)
    
    # Verify response still succeeds
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert len(body) == 1
    
    # Verify user is included with null details
    user = body[0]
    assert user['userId'] == 'deleted-user'
    assert user['username'] is None
    assert user['email'] is None


@mock_aws
def test_no_user_pool_id_returns_user_ids_only():
    """Test that without USER_POOL_ID, only user IDs are returned."""
    db_module._client = None
    
    # Remove USER_POOL_ID
    del os.environ['USER_POOL_ID']
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    setup_dynamodb_tables(dynamodb)
    
    # Create interests
    interests_table = dynamodb.Table('test-interests')
    interests_table.put_item(Item={
        'userId': 'user-1',
        'movieId': 'movie-123',
        'createdAt': 1000
    })
    interests_table.put_item(Item={
        'userId': 'user-2',
        'movieId': 'movie-123',
        'createdAt': 1001
    })
    
    # Call handler
    event = create_test_event('movie-123')
    context = create_lambda_context()
    response = lambda_handler(event, context)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert len(body) == 2
    
    # Verify only userId is present
    for user in body:
        assert 'userId' in user
        assert len(user) == 1  # Only userId field


@mock_aws
def test_missing_movie_id():
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
@patch('boto3.client')
def test_mixed_valid_and_deleted_users(mock_boto_client):
    """Test handling of mix of valid and deleted Cognito users."""
    db_module._client = None
    
    # Mock Cognito client
    mock_cognito = MagicMock()
    mock_boto_client.return_value = mock_cognito
    
    # Set up mixed responses
    def admin_get_user_side_effect(UserPoolId, Username):
        if Username == 'user-1':
            return {
                'Username': 'user-1',
                'UserAttributes': [
                    {'Name': 'email', 'Value': 'user1@example.com'}
                ]
            }
        else:
            from botocore.exceptions import ClientError
            raise ClientError(
                {'Error': {'Code': 'UserNotFoundException', 'Message': 'User not found'}},
                'AdminGetUser'
            )
    
    mock_cognito.admin_get_user.side_effect = admin_get_user_side_effect
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    setup_dynamodb_tables(dynamodb)
    
    # Create interests
    interests_table = dynamodb.Table('test-interests')
    interests_table.put_item(Item={
        'userId': 'user-1',
        'movieId': 'movie-123',
        'createdAt': 1000
    })
    interests_table.put_item(Item={
        'userId': 'deleted-user',
        'movieId': 'movie-123',
        'createdAt': 1001
    })
    
    # Call handler
    event = create_test_event('movie-123')
    context = create_lambda_context()
    response = lambda_handler(event, context)
    
    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert len(body) == 2
    
    # Verify valid user has details
    user1 = next(u for u in body if u['userId'] == 'user-1')
    assert user1['email'] == 'user1@example.com'
    
    # Verify deleted user has null details
    deleted_user = next(u for u in body if u['userId'] == 'deleted-user')
    assert deleted_user['username'] is None
    assert deleted_user['email'] is None
