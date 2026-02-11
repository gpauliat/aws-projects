"""
End-to-end integration tests for the Movie Download Wishlist application.

These tests run against the deployed AWS infrastructure and validate:
- Complete user flows from authentication to data operations
- Multi-user scenarios and concurrent access
- Data consistency across all operations

Requirements: 7.1, 7.2, 7.3

Setup:
    export AWS_REGION=eu-west-3
    export USER_POOL_ID=<your-user-pool-id>
    export CLIENT_ID=<your-client-id>
    export API_ENDPOINT=<your-api-gateway-url>
    
Run:
    pytest lambda/tests/test_integration_e2e.py -v
"""

import os
import pytest
import boto3
import requests
import time
import uuid
from datetime import datetime
from pycognito import Cognito


# Configuration from environment variables
AWS_REGION = os.environ.get('AWS_REGION', 'eu-west-3')
USER_POOL_ID = os.environ.get('USER_POOL_ID')
CLIENT_ID = os.environ.get('CLIENT_ID')
API_ENDPOINT = os.environ.get('API_ENDPOINT')
MOVIES_TABLE_NAME = os.environ.get('MOVIES_TABLE_NAME', 'movie-wishlist-dev-movies')
INTERESTS_TABLE_NAME = os.environ.get('INTERESTS_TABLE_NAME', 'movie-wishlist-dev-interests')


@pytest.fixture(scope='module')
def cognito_client():
    """Create Cognito client for user management."""
    return boto3.client('cognito-idp', region_name=AWS_REGION)


@pytest.fixture(scope='module')
def dynamodb_client():
    """Create DynamoDB client for data cleanup."""
    return boto3.resource('dynamodb', region_name=AWS_REGION)


@pytest.fixture(scope='module')
def test_user_a(cognito_client):
    """Create test user A and clean up after tests."""
    username = f'testuser_a_{uuid.uuid4().hex[:8]}'
    password = 'TestPass123!'
    
    # Create user
    cognito_client.admin_create_user(
        UserPoolId=USER_POOL_ID,
        Username=username,
        TemporaryPassword=password,
        MessageAction='SUPPRESS',
        UserAttributes=[
            {'Name': 'email', 'Value': f'{username}@example.com'}
        ]
    )
    
    # Set permanent password
    cognito_client.admin_set_user_password(
        UserPoolId=USER_POOL_ID,
        Username=username,
        Password=password,
        Permanent=True
    )
    
    yield {'username': username, 'password': password}
    
    # Cleanup: Delete user
    try:
        cognito_client.admin_delete_user(
            UserPoolId=USER_POOL_ID,
            Username=username
        )
    except Exception as e:
        print(f"Failed to delete user {username}: {e}")


@pytest.fixture(scope='module')
def test_user_b(cognito_client):
    """Create test user B and clean up after tests."""
    username = f'testuser_b_{uuid.uuid4().hex[:8]}'
    password = 'TestPass123!'
    
    # Create user
    cognito_client.admin_create_user(
        UserPoolId=USER_POOL_ID,
        Username=username,
        TemporaryPassword=password,
        MessageAction='SUPPRESS',
        UserAttributes=[
            {'Name': 'email', 'Value': f'{username}@example.com'}
        ]
    )
    
    # Set permanent password
    cognito_client.admin_set_user_password(
        UserPoolId=USER_POOL_ID,
        Username=username,
        Password=password,
        Permanent=True
    )
    
    yield {'username': username, 'password': password}
    
    # Cleanup: Delete user
    try:
        cognito_client.admin_delete_user(
            UserPoolId=USER_POOL_ID,
            Username=username
        )
    except Exception as e:
        print(f"Failed to delete user {username}: {e}")


def authenticate_user(username, password):
    """
    Authenticate a user and return the ID token.
    
    Returns:
        str: JWT ID token for API authentication
    """
    cognito = Cognito(
        user_pool_id=USER_POOL_ID,
        client_id=CLIENT_ID,
        username=username,
        user_pool_region=AWS_REGION
    )
    
    cognito.authenticate(password=password)
    return cognito.id_token


def cleanup_test_data(dynamodb_client):
    """Clean up all test data from DynamoDB tables."""
    movies_table = dynamodb_client.Table(MOVIES_TABLE_NAME)
    interests_table = dynamodb_client.Table(INTERESTS_TABLE_NAME)
    
    # Delete all movies
    response = movies_table.scan()
    for item in response.get('Items', []):
        movies_table.delete_item(Key={'movieId': item['movieId']})
    
    # Delete all interests
    response = interests_table.scan()
    for item in response.get('Items', []):
        interests_table.delete_item(Key={'userId': item['userId'], 'movieId': item['movieId']})


@pytest.fixture(autouse=True)
def cleanup_before_test(dynamodb_client):
    """Clean up test data before each test."""
    cleanup_test_data(dynamodb_client)
    yield
    cleanup_test_data(dynamodb_client)


class TestEndToEndUserFlow:
    """
    Test complete user flows from authentication to data operations.
    
    Validates: Requirements 7.1
    """
    
    def test_complete_user_flow_single_user(self, test_user_a):
        """
        Test: login → add movie → mark downloaded → add interest → logout
        
        Validates that a single user can perform all operations successfully.
        """
        # Step 1: Authenticate
        token = authenticate_user(test_user_a['username'], test_user_a['password'])
        assert token is not None, "Authentication failed"
        
        headers = {'Authorization': token}
        
        # Step 2: Verify empty movie list
        response = requests.get(f'{API_ENDPOINT}/movies', headers=headers)
        assert response.status_code == 200
        assert response.json() == []
        
        # Step 3: Add a movie
        movie_data = {'title': 'The Matrix'}
        response = requests.post(f'{API_ENDPOINT}/movies', json=movie_data, headers=headers)
        assert response.status_code == 201
        movie = response.json()
        assert movie['title'] == 'The Matrix'
        assert movie['status'] == 'wishlist'
        assert 'createdBy' in movie  # Verify createdBy field exists (contains Cognito sub)
        movie_id = movie['movieId']
        
        # Step 4: Verify movie appears in list
        response = requests.get(f'{API_ENDPOINT}/movies', headers=headers)
        assert response.status_code == 200
        movies = response.json()
        assert len(movies) == 1
        assert movies[0]['movieId'] == movie_id
        
        # Step 5: Mark movie as downloaded
        status_data = {'status': 'downloaded'}
        response = requests.patch(
            f'{API_ENDPOINT}/movies/{movie_id}/status',
            json=status_data,
            headers=headers
        )
        assert response.status_code == 200
        updated_movie = response.json()
        assert updated_movie['status'] == 'downloaded'
        
        # Step 6: Add interest to the movie
        response = requests.post(
            f'{API_ENDPOINT}/movies/{movie_id}/interest',
            headers=headers
        )
        assert response.status_code == 201
        
        # Step 7: Verify interest was recorded
        response = requests.get(
            f'{API_ENDPOINT}/movies/{movie_id}/interests',
            headers=headers
        )
        assert response.status_code == 200
        interested_users = response.json()
        assert len(interested_users) == 1
        assert 'userId' in interested_users[0]  # Verify userId field exists (contains Cognito sub)
        
        # Step 8: Remove interest
        response = requests.delete(
            f'{API_ENDPOINT}/movies/{movie_id}/interest',
            headers=headers
        )
        assert response.status_code == 204
        
        # Step 9: Verify interest was removed
        response = requests.get(
            f'{API_ENDPOINT}/movies/{movie_id}/interests',
            headers=headers
        )
        assert response.status_code == 200
        assert response.json() == []
        
        # Step 10: Delete movie
        response = requests.delete(f'{API_ENDPOINT}/movies/{movie_id}', headers=headers)
        assert response.status_code == 204
        
        # Step 11: Verify movie was deleted
        response = requests.get(f'{API_ENDPOINT}/movies', headers=headers)
        assert response.status_code == 200
        assert response.json() == []


class TestMultiUserScenarios:
    """
    Test multi-user scenarios and data visibility.
    
    Validates: Requirements 7.2
    """
    
    def test_multi_user_movie_interest(self, test_user_a, test_user_b):
        """
        Test: User A adds movie, User B expresses interest
        
        Validates that movies created by one user are visible to others
        and that multiple users can express interest.
        """
        # User A authenticates and adds a movie
        token_a = authenticate_user(test_user_a['username'], test_user_a['password'])
        headers_a = {'Authorization': token_a}
        
        movie_data = {'title': 'Inception'}
        response = requests.post(f'{API_ENDPOINT}/movies', json=movie_data, headers=headers_a)
        assert response.status_code == 201
        movie = response.json()
        movie_id = movie['movieId']
        
        # User B authenticates
        token_b = authenticate_user(test_user_b['username'], test_user_b['password'])
        headers_b = {'Authorization': token_b}
        
        # User B sees the movie
        response = requests.get(f'{API_ENDPOINT}/movies', headers=headers_b)
        assert response.status_code == 200
        movies = response.json()
        assert len(movies) == 1
        assert movies[0]['movieId'] == movie_id
        assert 'createdBy' in movies[0]  # Verify createdBy field exists
        
        # User B expresses interest
        response = requests.post(
            f'{API_ENDPOINT}/movies/{movie_id}/interest',
            headers=headers_b
        )
        assert response.status_code == 201
        
        # User A also expresses interest
        response = requests.post(
            f'{API_ENDPOINT}/movies/{movie_id}/interest',
            headers=headers_a
        )
        assert response.status_code == 201
        
        # Both users see all interested users
        response = requests.get(
            f'{API_ENDPOINT}/movies/{movie_id}/interests',
            headers=headers_a
        )
        assert response.status_code == 200
        interested_users = response.json()
        assert len(interested_users) == 2
        # Verify both users have userId fields (contains Cognito sub)
        for user in interested_users:
            assert 'userId' in user
    
    def test_concurrent_status_updates(self, test_user_a, test_user_b):
        """
        Test: Multiple users updating same movie status
        
        Validates that concurrent modifications are handled correctly.
        """
        # User A creates a movie
        token_a = authenticate_user(test_user_a['username'], test_user_a['password'])
        headers_a = {'Authorization': token_a}
        
        movie_data = {'title': 'Interstellar'}
        response = requests.post(f'{API_ENDPOINT}/movies', json=movie_data, headers=headers_a)
        assert response.status_code == 201
        movie_id = response.json()['movieId']
        
        # User B authenticates
        token_b = authenticate_user(test_user_b['username'], test_user_b['password'])
        headers_b = {'Authorization': token_b}
        
        # User A marks as downloaded
        status_data = {'status': 'downloaded'}
        response = requests.patch(
            f'{API_ENDPOINT}/movies/{movie_id}/status',
            json=status_data,
            headers=headers_a
        )
        assert response.status_code == 200
        
        # User B sees the updated status
        response = requests.get(f'{API_ENDPOINT}/movies', headers=headers_b)
        assert response.status_code == 200
        movies = response.json()
        assert len(movies) == 1
        assert movies[0]['status'] == 'downloaded'
        
        # User B changes it back to wishlist
        status_data = {'status': 'wishlist'}
        response = requests.patch(
            f'{API_ENDPOINT}/movies/{movie_id}/status',
            json=status_data,
            headers=headers_b
        )
        assert response.status_code == 200
        
        # User A sees the updated status
        response = requests.get(f'{API_ENDPOINT}/movies', headers=headers_a)
        assert response.status_code == 200
        movies = response.json()
        assert len(movies) == 1
        assert movies[0]['status'] == 'wishlist'


class TestDataConsistency:
    """
    Test data consistency across all operations.
    
    Validates: Requirements 7.3
    """
    
    def test_movie_deletion_removes_interests(self, test_user_a, test_user_b):
        """
        Test: Deleting a movie removes all associated interests
        
        Validates that the system maintains referential integrity.
        """
        # User A creates a movie
        token_a = authenticate_user(test_user_a['username'], test_user_a['password'])
        headers_a = {'Authorization': token_a}
        
        movie_data = {'title': 'The Dark Knight'}
        response = requests.post(f'{API_ENDPOINT}/movies', json=movie_data, headers=headers_a)
        assert response.status_code == 201
        movie_id = response.json()['movieId']
        
        # User B expresses interest
        token_b = authenticate_user(test_user_b['username'], test_user_b['password'])
        headers_b = {'Authorization': token_b}
        
        response = requests.post(
            f'{API_ENDPOINT}/movies/{movie_id}/interest',
            headers=headers_b
        )
        assert response.status_code == 201
        
        # User A also expresses interest
        response = requests.post(
            f'{API_ENDPOINT}/movies/{movie_id}/interest',
            headers=headers_a
        )
        assert response.status_code == 201
        
        # Verify interests exist
        response = requests.get(
            f'{API_ENDPOINT}/movies/{movie_id}/interests',
            headers=headers_a
        )
        assert response.status_code == 200
        assert len(response.json()) == 2
        
        # User A deletes the movie
        response = requests.delete(f'{API_ENDPOINT}/movies/{movie_id}', headers=headers_a)
        assert response.status_code == 204
        
        # Verify movie is gone
        response = requests.get(f'{API_ENDPOINT}/movies', headers=headers_a)
        assert response.status_code == 200
        assert response.json() == []
        
        # Verify interests are gone (should return empty list or 404)
        response = requests.get(
            f'{API_ENDPOINT}/movies/{movie_id}/interests',
            headers=headers_a
        )
        # Either 200 with empty list or 404 is acceptable
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            assert response.json() == []
    
    def test_empty_title_validation(self, test_user_a):
        """
        Test: Empty titles are rejected
        
        Validates: Requirement 3.2
        """
        token = authenticate_user(test_user_a['username'], test_user_a['password'])
        headers = {'Authorization': token}
        
        # Try to add movie with empty title
        movie_data = {'title': ''}
        response = requests.post(f'{API_ENDPOINT}/movies', json=movie_data, headers=headers)
        assert response.status_code == 400
        
        # Try with whitespace only
        movie_data = {'title': '   '}
        response = requests.post(f'{API_ENDPOINT}/movies', json=movie_data, headers=headers)
        assert response.status_code == 400
        
        # Verify no movies were created
        response = requests.get(f'{API_ENDPOINT}/movies', headers=headers)
        assert response.status_code == 200
        assert response.json() == []
    
    def test_invalid_status_transition(self, test_user_a):
        """
        Test: Invalid status values are rejected
        
        Validates: Requirement 4.1, 4.2
        """
        token = authenticate_user(test_user_a['username'], test_user_a['password'])
        headers = {'Authorization': token}
        
        # Create a movie
        movie_data = {'title': 'Test Movie'}
        response = requests.post(f'{API_ENDPOINT}/movies', json=movie_data, headers=headers)
        assert response.status_code == 201
        movie_id = response.json()['movieId']
        
        # Try to set invalid status
        status_data = {'status': 'invalid_status'}
        response = requests.patch(
            f'{API_ENDPOINT}/movies/{movie_id}/status',
            json=status_data,
            headers=headers
        )
        assert response.status_code == 400
        
        # Verify status didn't change
        response = requests.get(f'{API_ENDPOINT}/movies', headers=headers)
        assert response.status_code == 200
        movies = response.json()
        assert len(movies) == 1
        assert movies[0]['status'] == 'wishlist'


class TestAuthenticationFlow:
    """
    Test authentication and authorization.
    
    Validates: Requirements 1.1, 1.2, 1.3
    """
    
    def test_unauthenticated_access_denied(self):
        """
        Test: Requests without authentication are rejected
        
        Validates: Requirement 1.1
        """
        # Try to access API without token
        response = requests.get(f'{API_ENDPOINT}/movies')
        assert response.status_code == 401
        
        # Try to create movie without token
        movie_data = {'title': 'Test Movie'}
        response = requests.post(f'{API_ENDPOINT}/movies', json=movie_data)
        assert response.status_code == 401
    
    def test_invalid_token_rejected(self):
        """
        Test: Invalid tokens are rejected
        
        Validates: Requirement 1.3
        """
        headers = {'Authorization': 'invalid_token_12345'}
        
        response = requests.get(f'{API_ENDPOINT}/movies', headers=headers)
        assert response.status_code == 401
    
    def test_valid_authentication(self, test_user_a):
        """
        Test: Valid credentials grant access
        
        Validates: Requirement 1.2
        """
        token = authenticate_user(test_user_a['username'], test_user_a['password'])
        assert token is not None
        
        headers = {'Authorization': token}
        response = requests.get(f'{API_ENDPOINT}/movies', headers=headers)
        assert response.status_code == 200
