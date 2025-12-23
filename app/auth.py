from fastapi import Depends, HTTPException, status, Header, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import APIKey
from app.services.api_key_service import validate_and_get_api_key

# Define API key security scheme for OpenAPI documentation
api_key_header = APIKeyHeader(
    name="X-API-Key",
    description="API key for authentication. Contact support to obtain an API key.",
    auto_error=False
)


async def get_api_key(
    x_api_key: Optional[str] = Security(api_key_header),
    db: Session = Depends(get_db)
) -> APIKey:
    """
    Validate API key from X-API-Key header.
    
    This dependency authenticates requests using an API key.
    All protected endpoints should include this dependency.
    
    Args:
        x_api_key: API key from X-API-Key header
        db: Database session for key validation
    
    Returns:
        APIKey: Validated API key object with project info
    
    Raises:
        HTTPException 401: If API key is missing or invalid
        
    Example:
        ```python
        @router.get("/protected")
        async def protected_endpoint(api_key: APIKey = Depends(get_api_key)):
            return {"project": api_key.project_name}
        ```
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required. Provide X-API-Key header."
        )

    # Use bcrypt verification to validate the plaintext API key against stored hashes
    api_key = validate_and_get_api_key(db, x_api_key)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key"
        )

    return api_key


async def get_admin_api_key(
    api_key: APIKey = Depends(get_api_key)
) -> APIKey:
    """
    Validate admin-level API key.
    
    This dependency requires a valid API key with administrator privileges.
    Use this for endpoints that perform administrative operations like:
    - Reviewing and approving feedback
    - Triggering maintenance tasks
    - Accessing sensitive data
    
    Admin privileges are determined by:
    1. Metadata field contains `{"role": "admin"}`, OR
    2. Project name contains "admin"
    
    Args:
        api_key: Validated API key from get_api_key dependency
    
    Returns:
        APIKey: Validated admin API key object
    
    Raises:
        HTTPException 401: If API key is missing or invalid
        HTTPException 403: If API key is valid but not admin-level
        
    Example:
        ```python
        @router.post("/admin/approve")
        async def admin_endpoint(admin_key: APIKey = Depends(get_admin_api_key)):
            return {"admin": admin_key.project_name}
        ```
    """
    # Check if API key has admin role in metadata
    if api_key.metadata and isinstance(api_key.metadata, dict):
        if api_key.metadata.get("role") == "admin":
            return api_key
    
    # Alternative: check if project_name indicates admin access
    if api_key.project_name and "admin" in api_key.project_name.lower():
        return api_key
    
    # If neither condition is met, deny access
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin privileges required. This endpoint requires an admin-level API key."
    )
