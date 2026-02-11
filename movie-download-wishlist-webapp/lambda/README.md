# Movie Download Wishlist - Lambda Functions

This directory contains all AWS Lambda functions for the Movie Download Wishlist application.

## Structure

```
lambda/
├── requirements.txt          # Python dependencies
├── src/
│   ├── shared/              # Shared utilities
│   │   ├── response.py      # API response helpers
│   │   ├── dynamodb_client.py  # DynamoDB client wrapper
│   │   └── validation.py    # Input validation utilities
│   ├── create_movie.py      # Lambda: Create new movie
│   ├── get_movies.py        # Lambda: Get all movies
│   ├── update_movie_status.py # Lambda: Update movie status
│   ├── delete_movie.py      # Lambda: Delete movie
│   ├── add_interest.py      # Lambda: Add user interest
│   ├── remove_interest.py   # Lambda: Remove user interest
│   └── get_interested_users.py # Lambda: Get interested users
└── tests/                   # Unit and property-based tests
```

## Shared Utilities

### response.py
Provides standardized API Gateway response formatting:
- `success_response()` - 200/201 responses with JSON body
- `error_response()` - Error responses with consistent format
- `no_content_response()` - 204 No Content responses

### dynamodb_client.py
DynamoDB client wrapper with:
- Centralized table access
- Error handling and HTTP status code mapping
- Singleton pattern for connection reuse

### validation.py
Input validation utilities:
- `validate_movie_title()` - Validate movie titles
- `validate_movie_status()` - Validate status values
- `validate_uuid()` - Basic UUID format validation

## Development

### Install Dependencies

```bash
cd lambda
pip install -r requirements.txt
```

### Run Tests

```bash
# Unit tests
pytest tests/

# With coverage
pytest --cov=src tests/

# Property-based tests only
pytest -m property tests/
```

## Environment Variables

Each Lambda function requires:
- `MOVIES_TABLE_NAME` - DynamoDB Movies table name
- `INTERESTS_TABLE_NAME` - DynamoDB Interests table name
- `USER_POOL_ID` - Cognito User Pool ID (for getInterestedUsers)

These are set automatically by Terraform during deployment.

## Lambda Functions

Each function is a single Python file in `src/` (e.g., `create_movie.py`, `get_movies.py`).

The handler function signature:
```python
def lambda_handler(event, context):
    """
    Args:
        event: API Gateway event with body, pathParameters, requestContext
        context: Lambda context object
    
    Returns:
        API Gateway response dictionary
    """
```

## Testing Strategy

- **Unit Tests**: Test specific examples and edge cases
- **Property-Based Tests**: Test universal properties with Hypothesis
- **Integration Tests**: Test with LocalStack or AWS test environment

See individual test files for property definitions and test coverage.
