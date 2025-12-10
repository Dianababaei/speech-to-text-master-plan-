"""
Authentication dependencies for FastAPI endpoints.

This module provides dependency functions for validating API keys
and securing protected endpoints.
"""

import logging
from typing import Annotated, Optional
from datetime import datetime

from fastapi import Depends, HTTPException, Header, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.api_key import ApiKey
from app.services.api_key_service import verify_api_key
from app.config.settings import get_settings

# Configure logging
logger = logging.getLogger(__name__)
settings = get_settings()


class AuthenticationError(Exception):
    """Base exception for authentication errors."""
    pass


def get_current_api_key(
    x_api_key: Annotated[Optional[str], Header(alias="X-API-Key", description="API key for authentication")] = None,
    api_key: Annotated[Optional[str], Query(description="API key for authentication (fallback)")] = None,
    db: Session = Depends(get_db)
) -> ApiKey:
    """
    FastAPI dependency for API key authentication.

    Validates API key from header (primary) or query parameter (fallback).
    Updates last_used_at timestamp on successful authentication.

    Args:
        x_api_key: API key from X-API-Key header (primary)
        api_key: API key from query parameter (fallback)
        db: Database session

    Returns:
        ApiKey: The validated API key model object

    Raises:
        HTTPException: 401 if authentication fails

    Usage:
        @app.get("/protected")
        def protected_endpoint(
            current_api_key: ApiKey = Depends(get_current_api_key)
        ):
            return {"message": "Access granted"}
    """
    # Extract API key from header or query param
    plaintext_key = x_api_key or api_key

    # Missing API key
    if not plaintext_key:
        logger.warning("Authentication failed: No API key provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide X-API-Key header or api_key query parameter.",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    # Validate API key format (basic check)
    if len(plaintext_key) < 10:
        logger.warning(f"Authentication failed: Invalid API key format (too short)")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
            headers={"WWW-Authenticate": "ApiKey"}
        )

    try:
        # Query all active API keys
        # Note: We query all active keys and verify hashes to prevent timing attacks
        active_keys = db.query(ApiKey).filter(ApiKey.is_active == True).all()

        if not active_keys:
            logger.warning("Authentication failed: No active API keys in database")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "ApiKey"}
            )

        # Verify against each active key
        authenticated_key = None
        for key_record in active_keys:
            try:
                if verify_api_key(plaintext_key, key_record.key_hash):
                    authenticated_key = key_record
                    break
            except Exception as e:
                # Log verification error but continue checking other keys
                logger.error(f"Error verifying key {key_record.id}: {str(e)}")
                continue

        # No matching key found
        if not authenticated_key:
            logger.warning(f"Authentication failed: Invalid API key")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "ApiKey"}
            )

        # Additional check: Ensure key is still active (defensive)
        if not authenticated_key.is_active:
            logger.warning(
                f"Authentication failed: API key {authenticated_key.id} is inactive",
                extra={"api_key_id": str(authenticated_key.id)}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key has been deactivated",
                headers={"WWW-Authenticate": "ApiKey"}
            )

        # Update last_used_at timestamp
        try:
            authenticated_key.last_used_at = datetime.utcnow()
            db.commit()
            db.refresh(authenticated_key)
        except Exception as e:
            # Don't fail authentication if timestamp update fails
            # Just log the error and continue
            logger.error(
                f"Failed to update last_used_at for key {authenticated_key.id}: {str(e)}",
                extra={"api_key_id": str(authenticated_key.id)}
            )
            db.rollback()

        # Log successful authentication
        logger.info(
            f"Authentication successful",
            extra={
                "api_key_id": str(authenticated_key.id),
                "project_name": authenticated_key.project_name
            }
        )

        return authenticated_key

    except HTTPException:
        # Re-raise HTTP exceptions (authentication failures)
        raise
    except Exception as e:
        # Database or unexpected errors
        logger.error(
            f"Authentication error: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


def get_api_key_id(
    current_api_key: ApiKey = Depends(get_current_api_key)
) -> int:
    """
    Convenience dependency that returns just the API key ID.

    This is useful for endpoints that only need the key ID rather than
    the full ApiKey object.

    Args:
        current_api_key: Authenticated API key from get_current_api_key

    Returns:
        int: The API key ID

    Usage:
        @app.post("/jobs")
        def create_job(api_key_id: int = Depends(get_api_key_id)):
            # Use api_key_id
            pass
    """
    return current_api_key.id


def require_active_api_key(
    current_api_key: ApiKey = Depends(get_current_api_key)
) -> ApiKey:
    """
    Dependency that requires an active API key.

    This is an alias for get_current_api_key with a more explicit name.
    Use this when you want to make it clear that the endpoint requires auth.

    Args:
        current_api_key: Authenticated API key

    Returns:
        ApiKey: The validated API key model object

    Usage:
        @app.get("/protected")
        def protected_endpoint(
            api_key: ApiKey = Depends(require_active_api_key)
        ):
            return {"project": api_key.project_name}
    """
    return current_api_key


def verify_admin_key(
    x_admin_key: Annotated[Optional[str], Header(alias="X-Admin-Key", description="Admin API key for authentication")] = None
) -> bool:
    """
    FastAPI dependency for admin authentication.

    Validates admin API key from X-Admin-Key header against the master admin key
    stored in environment variable ADMIN_API_KEY.

    Args:
        x_admin_key: Admin key from X-Admin-Key header

    Returns:
        bool: True if authenticated

    Raises:
        HTTPException: 403 if authentication fails, 500 if admin key not configured

    Usage:
        @app.post("/admin/api-keys")
        def admin_endpoint(
            _: bool = Depends(verify_admin_key)
        ):
            return {"message": "Admin access granted"}

    Security Notes:
        - The ADMIN_API_KEY environment variable must be set
        - Store the admin key securely (use secrets manager in production)
        - All admin actions are logged for audit trail
    """
    # Get admin key from settings
    admin_key = settings.ADMIN_API_KEY

    # Check if admin key is configured
    if not admin_key:
        logger.error("Admin authentication failed: ADMIN_API_KEY not configured")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin authentication not configured. Set ADMIN_API_KEY environment variable."
        )

    # Check if admin key was provided
    if not x_admin_key:
        logger.warning("Admin authentication failed: No admin key provided")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing admin credentials. Provide X-Admin-Key header."
        )

    # Verify admin key matches
    if x_admin_key != admin_key:
        logger.warning("Admin authentication failed: Invalid admin key")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin credentials"
        )

    # Log successful admin authentication
    logger.info("Admin authentication successful")

    return True
