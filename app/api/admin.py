"""
Admin endpoints for API key management.

These endpoints are protected by admin authentication and should not be
publicly accessible in production environments.

All admin actions are logged for audit trail purposes.
"""

import logging
from typing import Annotated, Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.services.api_key_service import create_api_key, APIKeyError, APIKeyValidationError
from app.models.api_key import ApiKey
from app.dependencies.auth import verify_admin_key

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateAPIKeyRequest(BaseModel):
    """Request model for creating a new API key."""
    project_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable identifier for the project/application"
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional detailed description of the key's purpose"
    )
    rate_limit: int = Field(
        100,
        gt=0,
        le=10000,
        description="Maximum requests per minute (default: 100, max: 10000)"
    )

    @field_validator('project_name')
    @classmethod
    def validate_project_name(cls, v: str) -> str:
        """Validate project name is not empty after stripping whitespace."""
        if not v.strip():
            raise ValueError('project_name cannot be empty or whitespace')
        return v.strip()

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "project_name": "Mobile App Production",
                "description": "API key for production mobile application",
                "rate_limit": 1000
            }
        }


class CreateAPIKeyResponse(BaseModel):
    """Response model for API key creation."""
    api_key: str = Field(
        ...,
        description="The plaintext API key - save this immediately, it cannot be retrieved again"
    )
    key_id: int = Field(
        ...,
        description="Unique identifier for this API key"
    )
    project_name: str = Field(
        ...,
        description="Project name associated with this key"
    )
    rate_limit: int = Field(
        ...,
        description="Requests per minute limit for this key"
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the key was created"
    )
    warning: str = Field(
        default="This API key will only be shown once. Store it securely - it cannot be retrieved again.",
        description="Security warning about key storage"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "api_key": "Xg8K7HpL9mN2vB4fR6tY3wQ5sA1dF8jK",
                "key_id": 123,
                "project_name": "Mobile App Production",
                "rate_limit": 1000,
                "created_at": "2025-12-02T23:00:00Z",
                "warning": "This API key will only be shown once. Store it securely - it cannot be retrieved again."
            }
        }


class APIKeyListItem(BaseModel):
    """Model for API key in list response."""
    key_id: int = Field(..., description="Unique identifier for the API key")
    project_name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Key description")
    is_active: bool = Field(..., description="Whether the key is active")
    rate_limit: int = Field(..., description="Requests per minute limit")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_used_at: Optional[datetime] = Field(None, description="Last usage timestamp")
    key_hash_preview: str = Field(..., description="Masked preview of key hash for identification")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class APIKeyListResponse(BaseModel):
    """Response model for listing API keys."""
    total: int = Field(..., description="Total number of keys matching filter")
    limit: int = Field(..., description="Limit used for pagination")
    offset: int = Field(..., description="Offset used for pagination")
    items: List[APIKeyListItem] = Field(..., description="List of API keys")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "total": 5,
                "limit": 10,
                "offset": 0,
                "items": [
                    {
                        "key_id": 123,
                        "project_name": "Mobile App Production",
                        "description": "Production API key",
                        "is_active": True,
                        "rate_limit": 1000,
                        "created_at": "2025-12-02T23:00:00Z",
                        "updated_at": "2025-12-02T23:00:00Z",
                        "last_used_at": "2025-12-02T23:30:00Z",
                        "key_hash_preview": "$2b$12$abc...xyz"
                    }
                ]
            }
        }


class UpdateAPIKeyRequest(BaseModel):
    """Request model for updating an API key."""
    project_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="New project name (optional)"
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="New description (optional)"
    )
    rate_limit: Optional[int] = Field(
        None,
        gt=0,
        le=10000,
        description="New rate limit (optional)"
    )
    is_active: Optional[bool] = Field(
        None,
        description="Whether the key should be active (optional)"
    )

    @field_validator('project_name')
    @classmethod
    def validate_project_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate project name is not empty after stripping whitespace."""
        if v is not None and not v.strip():
            raise ValueError('project_name cannot be empty or whitespace')
        return v.strip() if v else None

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "project_name": "Mobile App Staging",
                "rate_limit": 500,
                "is_active": True
            }
        }


class UpdateAPIKeyResponse(BaseModel):
    """Response model for API key update."""
    key_id: int = Field(..., description="Unique identifier for the API key")
    project_name: str = Field(..., description="Project name")
    description: Optional[str] = Field(None, description="Key description")
    is_active: bool = Field(..., description="Whether the key is active")
    rate_limit: int = Field(..., description="Requests per minute limit")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        """Pydantic configuration."""
        from_attributes = True


class DeleteAPIKeyResponse(BaseModel):
    """Response model for API key deletion."""
    success: bool = Field(..., description="Whether deletion was successful")
    message: str = Field(..., description="Status message")
    key_id: int = Field(..., description="ID of the deleted key")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "API key deactivated successfully",
                "key_id": 123
            }
        }


# ============================================================================
# Helper Functions
# ============================================================================

def mask_key_hash(key_hash: str, visible_chars: int = 12) -> str:
    """
    Mask a key hash for display, showing only first few characters.

    Args:
        key_hash: The full key hash
        visible_chars: Number of characters to show (default: 12)

    Returns:
        str: Masked hash like "$2b$12$abc...xyz"
    """
    if len(key_hash) <= visible_chars + 3:
        return key_hash
    return f"{key_hash[:visible_chars]}...{key_hash[-3:]}"


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "/api-keys",
    response_model=CreateAPIKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new API key",
    description="Generate a new API key for a project. Requires admin authentication."
)
async def create_new_api_key(
    request: CreateAPIKeyRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[bool, Depends(verify_admin_key)]
) -> CreateAPIKeyResponse:
    """
    Create a new API key for a project.

    **Security:**
    - Requires X-Admin-Key header with valid admin credentials
    - The plaintext API key is returned only once and cannot be retrieved later
    - Store the returned API key securely

    **Request Body:**
    - **project_name**: Required, 1-255 characters
    - **description**: Optional description
    - **rate_limit**: Requests per minute limit (1-10000, default: 100)

    **Response:**
    - Returns the plaintext API key, key ID, and metadata
    - **Important:** Save the API key immediately - it will never be shown again

    **Authentication:**
    - Include X-Admin-Key header with master admin key
    """
    try:
        logger.info(
            f"Admin action: Creating new API key for project '{request.project_name}'",
            extra={"project_name": request.project_name, "rate_limit": request.rate_limit}
        )

        # Create the API key
        plaintext_key, api_key_record = create_api_key(
            db=db,
            project_name=request.project_name,
            description=request.description,
            rate_limit=request.rate_limit
        )

        logger.info(
            f"Admin action: API key created successfully",
            extra={"key_id": api_key_record.id, "project_name": api_key_record.project_name}
        )

        # Return response with plaintext key
        return CreateAPIKeyResponse(
            api_key=plaintext_key,
            key_id=api_key_record.id,
            project_name=api_key_record.project_name,
            rate_limit=api_key_record.rate_limit,
            created_at=api_key_record.created_at
        )

    except APIKeyValidationError as e:
        logger.warning(f"Admin action: API key creation failed - validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except APIKeyError as e:
        logger.error(f"Admin action: API key creation failed - service error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Admin action: API key creation failed - unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error creating API key: {str(e)}"
        )


@router.get(
    "/api-keys",
    response_model=APIKeyListResponse,
    summary="List all API keys",
    description="Get a paginated list of API keys with optional filtering. Requires admin authentication."
)
async def list_api_keys(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[bool, Depends(verify_admin_key)],
    is_active: Annotated[Optional[bool], Query(description="Filter by active status")] = None,
    limit: Annotated[int, Query(description="Maximum number of keys to return", ge=1, le=100)] = 10,
    offset: Annotated[int, Query(description="Number of keys to skip for pagination", ge=0)] = 0
) -> APIKeyListResponse:
    """
    List all API keys with optional filtering and pagination.

    **Security:**
    - Requires X-Admin-Key header with valid admin credentials

    **Query Parameters:**
    - **is_active**: Optional filter by active status (true/false)
    - **limit**: Maximum number of keys to return (1-100, default: 10)
    - **offset**: Number of keys to skip for pagination (default: 0)

    **Response:**
    - Returns paginated list of API keys with metadata
    - Key hashes are masked for security
    - Includes usage statistics (last_used_at)

    **Authentication:**
    - Include X-Admin-Key header with master admin key
    """
    try:
        logger.info(
            f"Admin action: Listing API keys",
            extra={"is_active": is_active, "limit": limit, "offset": offset}
        )

        # Build query
        query = db.query(ApiKey)

        # Apply filters
        if is_active is not None:
            query = query.filter(ApiKey.is_active == is_active)

        # Get total count
        total = query.count()

        # Apply pagination and order
        keys = query.order_by(ApiKey.created_at.desc()).limit(limit).offset(offset).all()

        # Convert to response format
        items = [
            APIKeyListItem(
                key_id=key.id,
                project_name=key.project_name,
                description=key.description,
                is_active=key.is_active,
                rate_limit=key.rate_limit,
                created_at=key.created_at,
                updated_at=key.updated_at,
                last_used_at=key.last_used_at,
                key_hash_preview=mask_key_hash(key.key_hash)
            )
            for key in keys
        ]

        logger.info(
            f"Admin action: Listed {len(items)} API keys (total: {total})",
            extra={"returned": len(items), "total": total}
        )

        return APIKeyListResponse(
            total=total,
            limit=limit,
            offset=offset,
            items=items
        )

    except SQLAlchemyError as e:
        logger.error(f"Admin action: Failed to list API keys - database error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while listing API keys"
        )
    except Exception as e:
        logger.error(f"Admin action: Failed to list API keys - unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error listing API keys: {str(e)}"
        )


@router.patch(
    "/api-keys/{key_id}",
    response_model=UpdateAPIKeyResponse,
    summary="Update an API key",
    description="Update API key metadata and settings. Requires admin authentication."
)
async def update_api_key(
    key_id: int,
    request: UpdateAPIKeyRequest,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[bool, Depends(verify_admin_key)]
) -> UpdateAPIKeyResponse:
    """
    Update an existing API key's metadata and settings.

    **Security:**
    - Requires X-Admin-Key header with valid admin credentials
    - Cannot update the API key itself (only metadata)

    **Path Parameters:**
    - **key_id**: The ID of the API key to update

    **Request Body (all fields optional):**
    - **project_name**: New project name
    - **description**: New description
    - **rate_limit**: New rate limit
    - **is_active**: Whether the key should be active

    **Response:**
    - Returns the updated API key metadata

    **Authentication:**
    - Include X-Admin-Key header with master admin key
    """
    try:
        logger.info(
            f"Admin action: Updating API key {key_id}",
            extra={"key_id": key_id}
        )

        # Get the API key
        api_key = db.query(ApiKey).filter(ApiKey.id == key_id).first()

        if not api_key:
            logger.warning(f"Admin action: API key {key_id} not found for update")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key with ID {key_id} not found"
            )

        # Track what fields are being updated
        updates = {}

        # Update only provided fields
        if request.project_name is not None:
            api_key.project_name = request.project_name
            updates["project_name"] = request.project_name

        if request.description is not None:
            api_key.description = request.description
            updates["description"] = request.description

        if request.rate_limit is not None:
            api_key.rate_limit = request.rate_limit
            updates["rate_limit"] = request.rate_limit

        if request.is_active is not None:
            api_key.is_active = request.is_active
            updates["is_active"] = request.is_active

        # Update timestamp
        api_key.updated_at = datetime.utcnow()

        # Commit changes
        db.commit()
        db.refresh(api_key)

        logger.info(
            f"Admin action: API key {key_id} updated successfully",
            extra={"key_id": key_id, "updates": updates}
        )

        return UpdateAPIKeyResponse(
            key_id=api_key.id,
            project_name=api_key.project_name,
            description=api_key.description,
            is_active=api_key.is_active,
            rate_limit=api_key.rate_limit,
            updated_at=api_key.updated_at
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except SQLAlchemyError as e:
        logger.error(f"Admin action: Failed to update API key {key_id} - database error: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while updating API key"
        )
    except Exception as e:
        logger.error(f"Admin action: Failed to update API key {key_id} - unexpected error: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error updating API key: {str(e)}"
        )


@router.delete(
    "/api-keys/{key_id}",
    response_model=DeleteAPIKeyResponse,
    summary="Delete an API key (soft delete)",
    description="Deactivate an API key. Requires admin authentication."
)
async def delete_api_key(
    key_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[bool, Depends(verify_admin_key)]
) -> DeleteAPIKeyResponse:
    """
    Delete (deactivate) an API key.

    This performs a soft delete by setting is_active=false rather than
    removing the record from the database. This preserves audit trail
    and allows for key reactivation if needed.

    **Security:**
    - Requires X-Admin-Key header with valid admin credentials

    **Path Parameters:**
    - **key_id**: The ID of the API key to delete

    **Response:**
    - Returns success status and message

    **Authentication:**
    - Include X-Admin-Key header with master admin key

    **Note:**
    - This is a soft delete (sets is_active=false)
    - The key record remains in the database for audit trail
    - Deactivated keys can be reactivated using PATCH endpoint
    """
    try:
        logger.info(
            f"Admin action: Deleting (deactivating) API key {key_id}",
            extra={"key_id": key_id}
        )

        # Get the API key
        api_key = db.query(ApiKey).filter(ApiKey.id == key_id).first()

        if not api_key:
            logger.warning(f"Admin action: API key {key_id} not found for deletion")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key with ID {key_id} not found"
            )

        # Soft delete: set is_active to false
        api_key.is_active = False
        api_key.updated_at = datetime.utcnow()

        # Commit changes
        db.commit()

        logger.info(
            f"Admin action: API key {key_id} deactivated successfully",
            extra={"key_id": key_id, "project_name": api_key.project_name}
        )

        return DeleteAPIKeyResponse(
            success=True,
            message="API key deactivated successfully",
            key_id=key_id
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except SQLAlchemyError as e:
        logger.error(f"Admin action: Failed to delete API key {key_id} - database error: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while deleting API key"
        )
    except Exception as e:
        logger.error(f"Admin action: Failed to delete API key {key_id} - unexpected error: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error deleting API key: {str(e)}"
        )


@router.get(
    "/health",
    summary="Admin health check",
    description="Verify admin authentication is working"
)
async def admin_health_check(
    _: Annotated[bool, Depends(verify_admin_key)]
):
    """
    Admin health check endpoint.

    Verifies that admin authentication is properly configured and working.

    **Authentication:**
    - Requires X-Admin-Key header with valid admin credentials
    """
    logger.info("Admin action: Health check")
    return {
        "status": "ok",
        "message": "Admin authentication is working"
    }
