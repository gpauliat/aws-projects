"""
DynamoDB client wrapper with error handling.
Provides centralized DynamoDB connection and error handling utilities.
"""

import os
import boto3
from botocore.exceptions import ClientError
from typing import Optional


class DynamoDBClient:
    """Wrapper for DynamoDB operations with error handling."""
    
    def __init__(self):
        """Initialize DynamoDB client and get table names from environment."""
        # Get region from environment or use default
        region = os.environ.get('AWS_REGION', os.environ.get('AWS_DEFAULT_REGION', 'eu-west-3'))
        self.dynamodb = boto3.resource('dynamodb', region_name=region)
        self.movies_table_name = os.environ.get('MOVIES_TABLE_NAME')
        self.interests_table_name = os.environ.get('INTERESTS_TABLE_NAME')
        
        if not self.movies_table_name:
            raise ValueError("MOVIES_TABLE_NAME environment variable not set")
        if not self.interests_table_name:
            raise ValueError("INTERESTS_TABLE_NAME environment variable not set")
        
        self.movies_table = self.dynamodb.Table(self.movies_table_name)
        self.interests_table = self.dynamodb.Table(self.interests_table_name)
    
    def handle_client_error(self, error: ClientError) -> tuple[int, str]:
        """
        Convert DynamoDB ClientError to HTTP status code and message.
        
        Args:
            error: boto3 ClientError exception
            
        Returns:
            Tuple of (status_code, error_message)
        """
        error_code = error.response['Error']['Code']
        
        if error_code == 'ConditionalCheckFailedException':
            return 409, "Resource conflict or condition not met"
        elif error_code == 'ResourceNotFoundException':
            return 404, "Resource not found"
        elif error_code == 'ProvisionedThroughputExceededException':
            return 503, "Service temporarily unavailable, please retry"
        elif error_code == 'ValidationException':
            return 400, "Invalid request parameters"
        elif error_code == 'TransactionCanceledException':
            return 500, "Transaction failed, please retry"
        else:
            return 500, "Internal server error"
    
    def is_throttling_error(self, error: ClientError) -> bool:
        """
        Check if error is a throttling error.
        
        Args:
            error: boto3 ClientError exception
            
        Returns:
            True if throttling error, False otherwise
        """
        error_code = error.response['Error']['Code']
        return error_code == 'ProvisionedThroughputExceededException'


# Singleton instance
_client: Optional[DynamoDBClient] = None


def get_dynamodb_client() -> DynamoDBClient:
    """
    Get or create DynamoDB client singleton.
    
    Returns:
        DynamoDBClient instance
    """
    global _client
    if _client is None:
        _client = DynamoDBClient()
    return _client
