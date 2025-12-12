from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import APIKey


async def get_api_key(
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> APIKey:
    """
    Dependency to validate API key from header.
    Raises 401 if API key is missing or invalid.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required. Provide X-API-Key header."
        )
    
    api_key = db.query(APIKey).filter(
        APIKey.key == x_api_key,
        APIKey.is_active == 1
    ).first()
    
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
    Dependency to validate admin-level API key.
    Requires a valid API key with admin privileges.
    
    Admin privileges are determined by checking if the metadata field
    contains {"role": "admin"} or if the project_name contains "admin".
    
    Raises 401 if API key is missing/invalid, 403 if not an admin key.
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
