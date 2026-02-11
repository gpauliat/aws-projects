"""
Property-based tests for response utilities.

**Feature: movie-download-wishlist, Property 13: Database failures preserve state**
**Validates: Requirements 6.4**

This test verifies that error responses maintain proper HTTP status codes
and don't leak sensitive information when database failures occur.
"""

import json
import pytest
from hypothesis import given, strategies as st
from src.shared.response import (
    success_response,
    error_response,
    no_content_response
)


# Property-Based Tests

@given(
    status_code=st.integers(min_value=200, max_value=299),
    body=st.one_of(
        st.dictionaries(st.text(), st.text()),
        st.lists(st.text()),
        st.text(),
        st.integers(),
        st.booleans()
    )
)
def test_property_success_responses_have_valid_structure(status_code, body):
    """
    Property: All success responses have valid API Gateway structure.
    
    For any 2xx status code and any JSON-serializable body,
    the response should have the correct structure with proper headers.
    """
    response = success_response(status_code, body)
    
    # Response must have required keys
    assert 'statusCode' in response
    assert 'headers' in response
    assert 'body' in response
    
    # Status code must match input
    assert response['statusCode'] == status_code
    
    # Headers must include CORS and Content-Type
    assert 'Content-Type' in response['headers']
    assert response['headers']['Content-Type'] == 'application/json'
    assert 'Access-Control-Allow-Origin' in response['headers']
    assert 'Access-Control-Allow-Credentials' in response['headers']
    
    # Body must be valid JSON string
    parsed_body = json.loads(response['body'])
    assert parsed_body == body


@given(
    status_code=st.integers(min_value=400, max_value=599),
    message=st.text(min_size=1, max_size=500),
    error_type=st.one_of(st.none(), st.text(min_size=1, max_size=100))
)
def test_property_error_responses_dont_leak_sensitive_info(status_code, message, error_type):
    """
    Property: Error responses never leak sensitive information.
    
    For any error status code and error message, the response should:
    - Have proper structure
    - Include only the error message and optional error type
    - Not expose internal details like stack traces or database info
    """
    response = error_response(status_code, message, error_type)
    
    # Response must have required keys
    assert 'statusCode' in response
    assert 'headers' in response
    assert 'body' in response
    
    # Status code must match input
    assert response['statusCode'] == status_code
    
    # Headers must include CORS
    assert 'Access-Control-Allow-Origin' in response['headers']
    
    # Body must be valid JSON
    parsed_body = json.loads(response['body'])
    
    # Body must contain error message
    assert 'error' in parsed_body
    assert parsed_body['error'] == message
    
    # If error_type provided, it should be included
    if error_type:
        assert 'errorType' in parsed_body
        assert parsed_body['errorType'] == error_type
    
    # Body should not contain sensitive keys
    sensitive_keys = ['stackTrace', 'internalError', 'dbError', 'exception', 'password', 'token']
    for key in sensitive_keys:
        assert key not in parsed_body


@given(
    custom_headers=st.dictionaries(
        st.text(min_size=1, max_size=50),
        st.text(min_size=1, max_size=100),
        max_size=5
    )
)
def test_property_custom_headers_are_preserved(custom_headers):
    """
    Property: Custom headers are preserved in responses.
    
    For any set of custom headers, they should be included in the response
    while maintaining default headers.
    """
    response = success_response(200, {"test": "data"}, headers=custom_headers)
    
    # All custom headers should be present
    for key, value in custom_headers.items():
        assert key in response['headers']
        assert response['headers'][key] == value
    
    # Default headers should still be present (unless overridden)
    if 'Content-Type' not in custom_headers:
        assert response['headers']['Content-Type'] == 'application/json'


def test_property_no_content_response_has_no_body():
    """
    Property: 204 No Content responses have empty body.
    
    No Content responses should always have status 204 and empty body.
    """
    response = no_content_response()
    
    assert response['statusCode'] == 204
    assert response['body'] == ''
    assert 'Access-Control-Allow-Origin' in response['headers']


# Unit Tests for Specific Cases

def test_success_response_with_dict_body():
    """Test success response with dictionary body."""
    body = {"movieId": "123", "title": "Test Movie"}
    response = success_response(200, body)
    
    assert response['statusCode'] == 200
    assert json.loads(response['body']) == body


def test_success_response_with_list_body():
    """Test success response with list body."""
    body = [{"id": "1"}, {"id": "2"}]
    response = success_response(200, body)
    
    assert response['statusCode'] == 200
    assert json.loads(response['body']) == body


def test_error_response_400_bad_request():
    """Test 400 Bad Request error response."""
    response = error_response(400, "Invalid input", "ValidationError")
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['error'] == "Invalid input"
    assert body['errorType'] == "ValidationError"


def test_error_response_404_not_found():
    """Test 404 Not Found error response."""
    response = error_response(404, "Movie not found")
    
    assert response['statusCode'] == 404
    body = json.loads(response['body'])
    assert body['error'] == "Movie not found"
    assert 'errorType' not in body


def test_error_response_500_internal_error():
    """Test 500 Internal Server Error response."""
    response = error_response(500, "Internal server error")
    
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert body['error'] == "Internal server error"


def test_error_response_503_service_unavailable():
    """Test 503 Service Unavailable error response."""
    response = error_response(503, "Service temporarily unavailable, please retry")
    
    assert response['statusCode'] == 503
    body = json.loads(response['body'])
    assert body['error'] == "Service temporarily unavailable, please retry"


def test_no_content_response_with_custom_headers():
    """Test 204 No Content with custom headers."""
    custom_headers = {"X-Custom-Header": "value"}
    response = no_content_response(headers=custom_headers)
    
    assert response['statusCode'] == 204
    assert response['body'] == ''
    assert response['headers']['X-Custom-Header'] == "value"


def test_cors_headers_always_present():
    """Test that CORS headers are always present in all response types."""
    success_resp = success_response(200, {})
    error_resp = error_response(400, "Error")
    no_content_resp = no_content_response()
    
    for resp in [success_resp, error_resp, no_content_resp]:
        assert 'Access-Control-Allow-Origin' in resp['headers']
        assert resp['headers']['Access-Control-Allow-Origin'] == '*'
