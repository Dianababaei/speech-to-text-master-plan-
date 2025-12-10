"""
FastAPI dependency functions for request processing.

This module provides reusable dependency functions that can be injected
into route handlers for common functionality like extracting lexicon IDs,
authentication, and database sessions.
"""

from typing import Optional
from fastapi import Header, Query

from app.config.settings import get_settings

settings = get_settings()


async def get_lexicon_id(
    x_lexicon_id: Optional[str] = Header(None, description="Lexicon ID for domain-specific processing"),
    lexicon: Optional[str] = Query(None, description="Lexicon ID (alternative to header)")
) -> str:
    """
    Extract lexicon_id from request header or query parameter.
    
    This dependency provides flexible lexicon selection via two methods:
    1. Request header: X-Lexicon-ID
    2. Query parameter: ?lexicon=
    
    The header takes precedence over the query parameter if both are provided.
    If neither is provided, returns the configured default lexicon.
    
    Args:
        x_lexicon_id: Lexicon ID from X-Lexicon-ID header (optional)
        lexicon: Lexicon ID from query parameter (optional)
        
    Returns:
        The selected lexicon_id (header > query > default)
        
    Example:
        ```python
        @app.post("/process")
        async def process_text(
            lexicon_id: str = Depends(get_lexicon_id)
        ):
            # Use lexicon_id for processing
            pass
        ```
    """
    # Header takes precedence, then query param, then default
    return x_lexicon_id or lexicon or settings.DEFAULT_LEXICON
