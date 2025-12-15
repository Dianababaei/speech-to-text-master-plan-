"""
Common error response models for OpenAPI documentation.

These models provide consistent error responses across all API endpoints.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Standard error response model for all API errors."""
    
    detail: str = Field(
        ...,
        description="Human-readable error message describing what went wrong",
        examples=["Invalid API key", "File size exceeds maximum allowed size"]
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "detail": "API key is required. Provide X-API-Key header."
                },
                {
                    "detail": "Invalid file format. Allowed formats: WAV, MP3, M4A"
                },
                {
                    "detail": "File size (15.50MB) exceeds maximum allowed size (10MB)"
                }
            ]
        }


class ValidationError(BaseModel):
    """Validation error detail for field-level errors."""
    
    loc: List[str] = Field(
        ...,
        description="Location of the error (field path)",
        examples=[["body", "term"], ["query", "page"]]
    )
    msg: str = Field(
        ...,
        description="Error message",
        examples=["field required", "value is not a valid integer"]
    )
    type: str = Field(
        ...,
        description="Error type",
        examples=["value_error", "type_error.integer"]
    )


class ValidationErrorResponse(BaseModel):
    """Response model for validation errors (422)."""
    
    detail: List[ValidationError] = Field(
        ...,
        description="List of validation errors"
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "detail": [
                        {
                            "loc": ["body", "term"],
                            "msg": "field required",
                            "type": "value_error.missing"
                        },
                        {
                            "loc": ["body", "replacement"],
                            "msg": "ensure this value has at least 1 characters",
                            "type": "value_error.any_str.min_length"
                        }
                    ]
                }
            ]
        }


class RateLimitError(BaseModel):
    """Rate limit error response with retry information."""
    
    detail: str = Field(
        ...,
        description="Rate limit error message",
        examples=["Rate limit exceeded. Please retry after 60 seconds."]
    )
    retry_after: Optional[int] = Field(
        None,
        description="Seconds to wait before retrying",
        examples=[60, 120]
    )
    limit: Optional[int] = Field(
        None,
        description="Maximum requests allowed in the time window",
        examples=[100, 1000]
    )
    remaining: Optional[int] = Field(
        0,
        description="Remaining requests in current time window"
    )
    reset: Optional[int] = Field(
        None,
        description="Unix timestamp when the rate limit resets",
        examples=[1705320000]
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "detail": "Rate limit exceeded. Please retry after 60 seconds.",
                    "retry_after": 60,
                    "limit": 100,
                    "remaining": 0,
                    "reset": 1705320000
                }
            ]
        }


class ServerError(BaseModel):
    """Server error response for 5xx errors."""
    
    detail: str = Field(
        ...,
        description="Error message",
        examples=["Internal server error", "Database connection failed"]
    )
    error_id: Optional[str] = Field(
        None,
        description="Unique error identifier for tracking",
        examples=["err_abc123xyz"]
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "detail": "Internal server error occurred. Please contact support.",
                    "error_id": "err_abc123xyz"
                },
                {
                    "detail": "Database connection failed",
                    "error_id": "err_db_timeout_456"
                }
            ]
        }


class ServiceUnavailable(BaseModel):
    """Service unavailable error response (503)."""
    
    detail: str = Field(
        ...,
        description="Service unavailability message",
        examples=["Service temporarily unavailable. Please try again later."]
    )
    retry_after: Optional[int] = Field(
        None,
        description="Seconds to wait before retrying",
        examples=[30, 60, 120]
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "detail": "Service temporarily unavailable. Please try again later.",
                    "retry_after": 60
                },
                {
                    "detail": "Database is currently unavailable",
                    "retry_after": 30
                }
            ]
        }


# Commonly used error responses for endpoints
ERROR_RESPONSES = {
    400: {
        "model": ErrorDetail,
        "description": "Bad Request - Invalid input or malformed request"
    },
    401: {
        "model": ErrorDetail,
        "description": "Unauthorized - Missing or invalid API key"
    },
    403: {
        "model": ErrorDetail,
        "description": "Forbidden - Insufficient permissions"
    },
    404: {
        "model": ErrorDetail,
        "description": "Not Found - Resource does not exist"
    },
    409: {
        "model": ErrorDetail,
        "description": "Conflict - Resource already exists or operation conflicts with current state"
    },
    413: {
        "model": ErrorDetail,
        "description": "Payload Too Large - File size exceeds maximum allowed"
    },
    422: {
        "model": ValidationErrorResponse,
        "description": "Unprocessable Entity - Validation error"
    },
    429: {
        "model": RateLimitError,
        "description": "Too Many Requests - Rate limit exceeded"
    },
    500: {
        "model": ServerError,
        "description": "Internal Server Error"
    },
    503: {
        "model": ServiceUnavailable,
        "description": "Service Unavailable - Temporary service interruption"
    }
}
