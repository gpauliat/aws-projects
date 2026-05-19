"""
Standardized API response helpers for Lambda functions.
Provides consistent response formatting across all endpoints.
"""

import json
from typing import Any, Dict, Optional
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle Decimal types from DynamoDB."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super(DecimalEncoder, self).default(obj)


def success_response(
    status_code: int,
    body: Any,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Create a successful API Gateway response.
    
    Args:
        status_code: HTTP status code (200, 201, etc.)
        body: Response body (will be JSON serialized)
        headers: Optional additional headers
        
    Returns:
        API Gateway response dictionary
    """
    default_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': 'true'
    }
    
    if headers:
        default_headers.update(headers)
    
    return {
        'statusCode': status_code,
        'headers': default_headers,
        'body': json.dumps(body, cls=DecimalEncoder)
    }


def error_response(
    status_code: int,
    message: str,
    error_type: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Create an error API Gateway response.
    
    Args:
        status_code: HTTP error status code (400, 404, 500, etc.)
        message: Human-readable error message
        error_type: Optional error type/code
        headers: Optional additional headers
        
    Returns:
        API Gateway response dictionary
    """
    default_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': 'true'
    }
    
    if headers:
        default_headers.update(headers)
    
    error_body = {
        'error': message
    }
    
    if error_type:
        error_body['errorType'] = error_type
    
    return {
        'statusCode': status_code,
        'headers': default_headers,
        'body': json.dumps(error_body)
    }


def no_content_response(headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Create a 204 No Content response.
    
    Args:
        headers: Optional additional headers
        
    Returns:
        API Gateway response dictionary
    """
    default_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': 'true'
    }
    
    if headers:
        default_headers.update(headers)
    
    return {
        'statusCode': 204,
        'headers': default_headers,
        'body': ''
    }
