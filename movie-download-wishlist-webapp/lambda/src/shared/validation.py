"""
Input validation utilities for Lambda functions.
Provides common validation functions for request data.
"""

from typing import Optional


def validate_movie_title(title: Optional[str]) -> tuple[bool, Optional[str]]:
    """
    Validate movie title is non-empty.
    
    Args:
        title: Movie title to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if title is None:
        return False, "Title is required"
    
    if not isinstance(title, str):
        return False, "Title must be a string"
    
    # Strip whitespace and check if empty
    if not title.strip():
        return False, "Title cannot be empty or whitespace only"
    
    if len(title.strip()) > 500:
        return False, "Title cannot exceed 500 characters"
    
    return True, None


def validate_movie_status(status: Optional[str]) -> tuple[bool, Optional[str]]:
    """
    Validate movie status is valid.
    
    Args:
        status: Movie status to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_statuses = ['wishlist', 'downloaded']
    
    if status is None:
        return False, "Status is required"
    
    if not isinstance(status, str):
        return False, "Status must be a string"
    
    if status not in valid_statuses:
        return False, f"Status must be one of: {', '.join(valid_statuses)}"
    
    return True, None


def validate_uuid(uuid_str: Optional[str], field_name: str = "ID") -> tuple[bool, Optional[str]]:
    """
    Validate UUID format (basic validation).
    
    Args:
        uuid_str: UUID string to validate
        field_name: Name of field for error message
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if uuid_str is None:
        return False, f"{field_name} is required"
    
    if not isinstance(uuid_str, str):
        return False, f"{field_name} must be a string"
    
    if not uuid_str.strip():
        return False, f"{field_name} cannot be empty"
    
    # Basic UUID format check (length and hyphens)
    if len(uuid_str) != 36 or uuid_str.count('-') != 4:
        return False, f"{field_name} must be a valid UUID"
    
    return True, None
