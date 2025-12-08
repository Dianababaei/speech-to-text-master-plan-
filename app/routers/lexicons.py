"""
Lexicon Discovery Router

This module provides REST API endpoints for browsing available lexicons
and retrieving metadata about domain-specific terminology collections.
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_api_key
from app.models.lexicon import LexiconListResponse, LexiconDetailResponse, LexiconMetadata
from app.services.lexicon_service import get_all_lexicons, get_lexicon_by_id

logger = logging.getLogger(__name__)

# Create router with authentication dependency
router = APIRouter(
    prefix="/lexicons",
    tags=["lexicons"],
    dependencies=[Depends(get_api_key)],  # Apply authentication to all endpoints
)


@router.get(
    "",
    response_model=LexiconListResponse,
    summary="List all available lexicons",
    description="""
    Retrieve metadata for all available domain-specific lexicons.
    
    Returns an array of lexicon objects, each containing:
    - `lexicon_id`: Unique identifier (e.g., "radiology", "cardiology", "general")
    - `term_count`: Number of active terms in the lexicon
    - `last_updated`: Timestamp of most recent term modification
    - `description`: Human-readable description
    
    Results are cached for 10 minutes to optimize performance.
    """,
    responses={
        200: {
            "description": "List of available lexicons with metadata",
            "content": {
                "application/json": {
                    "example": {
                        "lexicons": [
                            {
                                "lexicon_id": "radiology",
                                "term_count": 150,
                                "last_updated": "2024-01-15T10:30:00Z",
                                "description": "Medical radiology terminology"
                            },
                            {
                                "lexicon_id": "cardiology",
                                "term_count": 89,
                                "last_updated": "2024-01-14T08:15:00Z",
                                "description": "Cardiovascular and cardiac terminology"
                            }
                        ]
                    }
                }
            }
        },
        401: {"description": "Authentication failed - invalid or missing API key"}
    }
)
async def list_lexicons(
    db: Session = Depends(get_db)
) -> LexiconListResponse:
    """
    Get all available lexicons with metadata.
    
    Args:
        db: Database session (injected)
    
    Returns:
        LexiconListResponse: List of lexicons with metadata
    """
    try:
        logger.info("Fetching all lexicons")
        lexicons = get_all_lexicons(db, use_cache=True)
        
        logger.info(f"Returning {len(lexicons)} lexicons")
        return LexiconListResponse(lexicons=lexicons)
        
    except Exception as e:
        logger.error(f"Error fetching lexicons: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve lexicons"
        )


@router.get(
    "/{lexicon_id}",
    response_model=LexiconDetailResponse,
    summary="Get specific lexicon metadata",
    description="""
    Retrieve detailed metadata for a specific lexicon by its ID.
    
    Returns the same metadata fields as the list endpoint, but for a single lexicon.
    
    Results are cached for 10 minutes to optimize performance.
    """,
    responses={
        200: {
            "description": "Lexicon metadata",
            "content": {
                "application/json": {
                    "example": {
                        "lexicon_id": "radiology",
                        "term_count": 150,
                        "last_updated": "2024-01-15T10:30:00Z",
                        "description": "Medical radiology terminology"
                    }
                }
            }
        },
        404: {
            "description": "Lexicon not found or has no active terms",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Lexicon 'unknown' not found or has no active terms"
                    }
                }
            }
        },
        401: {"description": "Authentication failed - invalid or missing API key"}
    }
)
async def get_lexicon(
    lexicon_id: str,
    db: Session = Depends(get_db)
) -> LexiconDetailResponse:
    """
    Get metadata for a specific lexicon.
    
    Args:
        lexicon_id: Unique lexicon identifier (e.g., "radiology")
        db: Database session (injected)
    
    Returns:
        LexiconDetailResponse: Lexicon metadata
    
    Raises:
        HTTPException: 404 if lexicon not found or has no active terms
    """
    try:
        logger.info(f"Fetching lexicon: {lexicon_id}")
        lexicon = get_lexicon_by_id(db, lexicon_id, use_cache=True)
        
        if not lexicon:
            logger.warning(f"Lexicon not found: {lexicon_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Lexicon '{lexicon_id}' not found or has no active terms"
            )
        
        logger.info(f"Returning lexicon {lexicon_id} with {lexicon.term_count} terms")
        return LexiconDetailResponse(
            lexicon_id=lexicon.lexicon_id,
            term_count=lexicon.term_count,
            last_updated=lexicon.last_updated,
            description=lexicon.description
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching lexicon {lexicon_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve lexicon '{lexicon_id}'"
        )
