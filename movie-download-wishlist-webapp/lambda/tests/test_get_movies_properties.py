"""
Property-based tests for getMovies Lambda function.

**Feature: movie-download-wishlist, Property 6: Movie list retrieval returns all movies**
**Validates: Requirements 2.1, 2.2**

**Feature: movie-download-wishlist, Property 12: Multiple interests are tracked**
**Validates: Requirements 5.4**

These tests verify that:
- Any set of movies in DynamoDB is returned by getMovies
- All movies have correct titles and statuses
- All interested users are included for each movie
"""

import json
import os
import pytest
from hypothesis import given, strategies as st, settings, assume
from moto import mock_aws
import boto3

from src.get_movies import lambda_handler
import src.shared.dynamodb_client as db_module


@pytest.fixture(autouse=True)
def setup_environment():
    """Set up environment variables for all tests."""
    os.environ['MOVIES_TABLE_NAME'] = 'test-movies'
    os.environ['INTERESTS_TABLE_NAME'] = 'test-interests'
    os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    yield
    db_module._client = None


def create_test_event():
    """Helper to create API Gateway event."""
    return {
        'httpMethod': 'GET',
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
    context.function_name = 'getMovies'
    return context


def setup_dynamodb_tables(dynamodb):
    """Helper to create DynamoDB tables."""
    # Delete and recreate tables to ensure clean state
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
    
    # Create fresh tables
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


# Property 6: Movie list retrieval returns all movies
@mock_aws
@given(
    movies=st.lists(
        st.fixed_dictionaries({
            'movieId': st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789-'),
            'title': st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyz '),
            'status': st.sampled_from(['wishlist', 'downloaded']),
            'createdBy': st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789'),
            'createdAt': st.integers(min_value=1000, max_value=10000),
            'updatedAt': st.integers(min_value=1000, max_value=10000)
        }),
        min_size=0,
        max_size=5,
        unique_by=lambda x: x['movieId']
    )
)
@settings(max_examples=10, deadline=3000)
def test_property_get_movies_returns_all_movies(movies):
    """
    Property 6: Movie list retrieval returns all movies.
    
    For any set of movies in DynamoDB, calling getMovies should:
    - Return 200 status code
    - Return all movies with their titles and statuses
    - Include interestedUsers field for each movie
    """
    # Reset client
    db_module._client = None
    
    # Create DynamoDB tables
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    setup_dynamodb_tables(dynamodb)
    
    # Add movies to DynamoDB
    movies_table = dynamodb.Table('test-movies')
    for movie in movies:
        movies_table.put_item(Item=movie)
    
    # Call handler
    event = create_test_event()
    context = create_lambda_context()
    response = lambda_handler(event, context)
    
    # Verify response
    assert response['statusCode'] == 200
    
    body = json.loads(response['body'])
    assert isinstance(body, list)
    assert len(body) == len(movies)
    
    # Verify all movies are present
    returned_movie_ids = {m['movieId'] for m in body}
    expected_movie_ids = {m['movieId'] for m in movies}
    assert returned_movie_ids == expected_movie_ids
    
    # Verify each movie has required fields
    for movie in body:
        assert 'movieId' in movie
        assert 'title' in movie
        assert 'status' in movie
        assert movie['status'] in ['wishlist', 'downloaded']
        assert 'interestedUsers' in movie
        assert isinstance(movie['interestedUsers'], list)


# Property 12: Multiple interests are tracked
@mock_aws
@given(
    movie_data=st.fixed_dictionaries({
        'movieId': st.just('test-movie-123'),
        'title': st.just('Test Movie'),
        'status': st.just('wishlist'),
        'createdBy': st.just('user-creator'),
        'createdAt': st.just(1000),
        'updatedAt': st.just(1000)
    }),
    interested_users=st.lists(
        st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789'),
        min_size=0,
        max_size=5,
        unique=True
    )
)
@settings(max_examples=10, deadline=3000)
def test_property_multiple_interests_tracked(movie_data, interested_users):
    """
    Property 12: Multiple interests are tracked.
    
    For any movie with multiple users expressing interest,
    querying via getMovies should return all interested users.
    """
    # Reset client
    db_module._client = None
    
    # Create DynamoDB tables
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    setup_dynamodb_tables(dynamodb)
    
    # Add movie to DynamoDB
    movies_table = dynamodb.Table('test-movies')
    movies_table.put_item(Item=movie_data)
    
    # Add interests
    interests_table = dynamodb.Table('test-interests')
    for user_id in interested_users:
        interests_table.put_item(Item={
            'userId': user_id,
            'movieId': movie_data['movieId'],
            'createdAt': 1100
        })
    
    # Call handler
    event = create_test_event()
    context = create_lambda_context()
    response = lambda_handler(event, context)
    
    # Verify response
    assert response['statusCode'] == 200
    
    body = json.loads(response['body'])
    assert len(body) == 1
    
    movie = body[0]
    assert 'interestedUsers' in movie
    assert len(movie['interestedUsers']) == len(interested_users)
    
    # Verify all interested users are present
    returned_users = set(movie['interestedUsers'])
    expected_users = set(interested_users)
    assert returned_users == expected_users


# Property: Movies are sorted by creation date
@mock_aws
@given(
    movies=st.lists(
        st.fixed_dictionaries({
            'movieId': st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789-'),
            'title': st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyz '),
            'status': st.sampled_from(['wishlist', 'downloaded']),
            'createdBy': st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789'),
            'createdAt': st.integers(min_value=1000, max_value=10000),
            'updatedAt': st.integers(min_value=1000, max_value=10000)
        }),
        min_size=2,
        max_size=5,
        unique_by=lambda x: x['movieId']
    )
)
@settings(max_examples=10, deadline=3000)
def test_property_movies_sorted_by_creation_date(movies):
    """
    Property: Movies are sorted by creation date (newest first).
    
    For any set of movies with different creation dates,
    getMovies should return them sorted by createdAt descending.
    """
    # Ensure movies have different creation dates
    assume(len(set(m['createdAt'] for m in movies)) == len(movies))
    
    # Reset client
    db_module._client = None
    
    # Create DynamoDB tables
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    setup_dynamodb_tables(dynamodb)
    
    # Add movies to DynamoDB
    movies_table = dynamodb.Table('test-movies')
    for movie in movies:
        movies_table.put_item(Item=movie)
    
    # Call handler
    event = create_test_event()
    context = create_lambda_context()
    response = lambda_handler(event, context)
    
    # Verify response
    assert response['statusCode'] == 200
    
    body = json.loads(response['body'])
    
    # Verify sorting (newest first)
    creation_dates = [m['createdAt'] for m in body]
    assert creation_dates == sorted(creation_dates, reverse=True)


# Property: Empty database returns empty list
@mock_aws
def test_property_empty_database_returns_empty_list():
    """
    Property: Empty database returns empty list.
    
    When no movies exist in DynamoDB, getMovies should:
    - Return 200 status code
    - Return an empty array
    """
    # Reset client
    db_module._client = None
    
    # Create empty DynamoDB tables
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    setup_dynamodb_tables(dynamodb)
    
    # Call handler
    event = create_test_event()
    context = create_lambda_context()
    response = lambda_handler(event, context)
    
    # Verify response
    assert response['statusCode'] == 200
    
    body = json.loads(response['body'])
    assert isinstance(body, list)
    assert len(body) == 0


# Property: Each movie has interestedUsers field
@mock_aws
@given(
    num_movies=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=10, deadline=5000)
def test_property_all_movies_have_interested_users_field(num_movies):
    """
    Property: Every movie has an interestedUsers field.
    
    For any number of movies, each returned movie should have
    an interestedUsers field (even if empty).
    """
    # Reset client
    db_module._client = None
    
    # Create DynamoDB tables
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    setup_dynamodb_tables(dynamodb)
    
    # Add movies
    movies_table = dynamodb.Table('test-movies')
    for i in range(num_movies):
        movies_table.put_item(Item={
            'movieId': f'movie-{i}',
            'title': f'Movie {i}',
            'status': 'wishlist',
            'createdBy': 'user-123',
            'createdAt': 1000 + i,
            'updatedAt': 1000 + i
        })
    
    # Call handler
    event = create_test_event()
    context = create_lambda_context()
    response = lambda_handler(event, context)
    
    # Verify response
    body = json.loads(response['body'])
    
    # Every movie must have interestedUsers field
    for movie in body:
        assert 'interestedUsers' in movie
        assert isinstance(movie['interestedUsers'], list)
