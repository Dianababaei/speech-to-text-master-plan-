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
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> APIKey:
    """
    Dependency to validate admin-level API key from header.
    Raises 401 if API key is missing, invalid, or not admin.
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
    
    # Check for admin privileges
    if not getattr(api_key, 'is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin privileges required"
        )
    
    return api_key
