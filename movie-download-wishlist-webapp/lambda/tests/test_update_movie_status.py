"""
Tests for updateMovieStatus Lambda function.

**Feature: movie-download-wishlist, Property 9: Status transitions are bidirectional**
**Validates: Requirements 4.1, 4.2, 4.3**
"""

import json
import os
import pytest
from unittest.mock import Mock
from hypothesis import given, strategies as st, settings
from moto import mock_aws
import boto3

from src.update_movie_status import lambda_handler
import src.shared.dynamodb_client as db_module


@pytest.fixture(autouse=True)
def setup_environment():
    """Set up environment variables."""
    os.environ['MOVIES_TABLE_NAME'] = 'test-movies'
    os.environ['INTERESTS_TABLE_NAME'] = 'test-interests'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    yield
    db_module._client = None


def create_event(movie_id, status):
    """Helper to create API Gateway event."""
    return {
        'pathParameters': {'movieId': movie_id},
        'body': json.dumps({'status': status})
    }


def create_context():
    """Helper to create Lambda context."""
    context = Mock()
    context.function_name = 'updateMovieStatus'
    return context


# Unit Tests
@mock_aws
def test_update_status_wishlist_to_downloaded(monkeypatch):
    """Test updating status from wishlist to downloaded."""
    monkeypatch.setenv('MOVIES_TABLE_NAME', 'test-movies')
    monkeypatch.setenv('INTERESTS_TABLE_NAME', 'test-interests')
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.create_table(
        TableName='test-movies',
        KeySchema=[{'AttributeName': 'movieId', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'movieId', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    
    table.put_item(Item={
        'movieId': 'movie-1',
        'title': 'Test Movie',
        'status': 'wishlist',
        'createdBy': 'user-123',
        'createdAt': 1000,
        'updatedAt': 1000
    })
    
    event = create_event('movie-1', 'downloaded')
    response = lambda_handler(event, create_context())
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['status'] == 'downloaded'
    assert body['updatedAt'] > 1000


@mock_aws
def test_update_status_movie_not_found(monkeypatch):
    """Test updating non-existent movie."""
    monkeypatch.setenv('MOVIES_TABLE_NAME', 'test-movies')
    monkeypatch.setenv('INTERESTS_TABLE_NAME', 'test-interests')
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    dynamodb.create_table(
        TableName='test-movies',
        KeySchema=[{'AttributeName': 'movieId', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'movieId', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    
    event = create_event('nonexistent', 'downloaded')
    response = lambda_handler(event, create_context())
    
    assert response['statusCode'] == 404


def test_update_status_invalid_status():
    """Test updating with invalid status."""
    event = create_event('movie-1', 'invalid-status')
    response = lambda_handler(event, create_context())
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'error' in body


# Property 9: Status transitions are bidirectional
@mock_aws
@given(
    initial_status=st.sampled_from(['wishlist', 'downloaded'])
)
@settings(max_examples=10, deadline=3000)
def test_property_status_transitions_bidirectional(initial_status):
    """
    Property 9: Status transitions are bidirectional.
    
    For any movie, status can transition wishlist <-> downloaded and back.
    """
    db_module._client = None
    
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    
    # Delete table if exists
    try:
        table = dynamodb.Table('test-movies')
        table.delete()
    except:
        pass
    
    # Create fresh table
    table = dynamodb.create_table(
        TableName='test-movies',
        KeySchema=[{'AttributeName': 'movieId', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'movieId', 'AttributeType': 'S'}],
        BillingMode='PAY_PER_REQUEST'
    )
    
    # Create movie with initial status
    table.put_item(Item={
        'movieId': 'test-movie',
        'title': 'Test',
        'status': initial_status,
        'createdBy': 'user-123',
        'createdAt': 1000,
        'updatedAt': 1000
    })
    
    # Toggle to opposite status
    opposite_status = 'downloaded' if initial_status == 'wishlist' else 'wishlist'
    event1 = create_event('test-movie', opposite_status)
    response1 = lambda_handler(event1, create_context())
    
    assert response1['statusCode'] == 200
    body1 = json.loads(response1['body'])
    assert body1['status'] == opposite_status
    
    # Toggle back to original status
    event2 = create_event('test-movie', initial_status)
    response2 = lambda_handler(event2, create_context())
    
    assert response2['statusCode'] == 200
    body2 = json.loads(response2['body'])
    assert body2['status'] == initial_status
