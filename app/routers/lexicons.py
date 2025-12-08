"""
Lexicon Discovery Router

This module provides REST API endpoints for browsing available lexicons
and retrieving metadata about domain-specific terminology collections.
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
Lexicon Router

REST API endpoints for managing lexicon terms within specific lexicons.
"""

import re
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
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
from app.models.api_key import ApiKey
from app.schemas.lexicon import (
    TermCreate, 
    TermUpdate, 
    TermResponse, 
    TermListResponse
)
from app.services import lexicon_service


router = APIRouter(
    prefix="/lexicons",
    tags=["lexicons"],
    dependencies=[Depends(get_api_key)]
)


def validate_lexicon_id(lexicon_id: str) -> str:
    """
    Validate lexicon_id format.
    
    Args:
        lexicon_id: The lexicon identifier to validate
    
    Returns:
        str: The validated lexicon_id
    
    Raises:
        HTTPException: If lexicon_id is invalid
    """
    # Alphanumeric and hyphens/underscores only, max 100 chars
    if not lexicon_id or len(lexicon_id) > 100:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Lexicon ID must be between 1 and 100 characters"
        )
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', lexicon_id):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Lexicon ID must contain only alphanumeric characters, hyphens, and underscores"
        )
    
    return lexicon_id


@router.post(
    "/{lexicon_id}/terms",
    response_model=TermResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add new term to lexicon",
    description="Create a new term in the specified lexicon with validation for uniqueness"
)
async def create_term(
    lexicon_id: str = Path(..., description="Lexicon identifier (e.g., 'radiology', 'cardiology')"),
    term_data: TermCreate = ...,
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key)
):
    """
    Add a new term to a lexicon.
    
    - **lexicon_id**: Identifier for the lexicon (alphanumeric, hyphens, underscores)
    - **term**: The term to match in transcriptions
    - **replacement**: The corrected/replacement term
    
    Returns the created term with ID and timestamps.
    """
    # Validate lexicon_id format
    lexicon_id = validate_lexicon_id(lexicon_id)
    
    try:
        # Create term using service
        new_term = lexicon_service.create_term(db, lexicon_id, term_data)
        return new_term
    
    except ValueError as e:
        # Term already exists
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    
    except Exception as e:
        # Internal server error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create term: {str(e)}"
        )


@router.get(
    "/{lexicon_id}/terms",
    response_model=TermListResponse,
    summary="List all terms in lexicon",
    description="Get paginated list of active terms in the specified lexicon"
)
async def list_terms(
    lexicon_id: str = Path(..., description="Lexicon identifier"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(50, ge=1, le=100, description="Items per page (max 100)"),
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key)
):
    """
    List all active terms in a lexicon with pagination.
    
    - **lexicon_id**: Identifier for the lexicon
    - **page**: Page number (default: 1)
    - **limit**: Items per page (default: 50, max: 100)
    
    Returns paginated list of terms with total count.
    """
    # Validate lexicon_id format
    lexicon_id = validate_lexicon_id(lexicon_id)
    
    try:
        # Get terms using service
        terms, total = lexicon_service.get_terms(db, lexicon_id, page, limit)
        
        return TermListResponse(
            items=terms,
            total=total,
            page=page,
            limit=limit
        )
    
    except Exception as e:
        # Internal server error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve terms: {str(e)}"
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
    "/{lexicon_id}/terms/{term_id}",
    response_model=TermResponse,
    summary="Get specific term details",
    description="Retrieve full details of a specific term by ID"
)
async def get_term(
    lexicon_id: str = Path(..., description="Lexicon identifier"),
    term_id: int = Path(..., ge=1, description="Term ID"),
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key)
):
    """
    Get details of a specific term.
    
    - **lexicon_id**: Identifier for the lexicon
    - **term_id**: Unique identifier of the term
    
    Returns full term object including metadata.
    """
    # Validate lexicon_id format
    lexicon_id = validate_lexicon_id(lexicon_id)
    
    try:
        # Get term using service
        term = lexicon_service.get_term_by_id(db, lexicon_id, term_id)
        
        if not term:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Term with ID {term_id} not found in lexicon '{lexicon_id}'"
            )
        
        return term
    
    except HTTPException:
        raise
    
    except Exception as e:
        # Internal server error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve term: {str(e)}"
        )


@router.put(
    "/{lexicon_id}/terms/{term_id}",
    response_model=TermResponse,
    summary="Update existing term",
    description="Update term and replacement text, updates timestamp automatically"
)
async def update_term(
    lexicon_id: str = Path(..., description="Lexicon identifier"),
    term_id: int = Path(..., ge=1, description="Term ID"),
    term_data: TermUpdate = ...,
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key)
):
    """
    Update an existing term.
    
    - **lexicon_id**: Identifier for the lexicon
    - **term_id**: Unique identifier of the term to update
    - **term**: Updated term text
    - **replacement**: Updated replacement text
    
    Returns the updated term with new timestamp.
    """
    # Validate lexicon_id format
    lexicon_id = validate_lexicon_id(lexicon_id)
    
    try:
        # Update term using service
        updated_term = lexicon_service.update_term(db, lexicon_id, term_id, term_data)
        
        if not updated_term:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Term with ID {term_id} not found in lexicon '{lexicon_id}'"
            )
        
        return updated_term
    
    except ValueError as e:
        # Term already exists (duplicate)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    
    except HTTPException:
        raise
    
    except Exception as e:
        # Internal server error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update term: {str(e)}"
        )


@router.delete(
    "/{lexicon_id}/terms/{term_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft delete term",
    description="Mark term as inactive (soft delete) to maintain audit trail"
)
async def delete_term(
    lexicon_id: str = Path(..., description="Lexicon identifier"),
    term_id: int = Path(..., ge=1, description="Term ID"),
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key)
):
    """
    Soft delete a term by setting is_active=false.
    
    - **lexicon_id**: Identifier for the lexicon
    - **term_id**: Unique identifier of the term to delete
    
    Term is not removed from database, maintaining audit trail.
    """
    # Validate lexicon_id format
    lexicon_id = validate_lexicon_id(lexicon_id)
    
    try:
        # Soft delete term using service
        deleted = lexicon_service.soft_delete_term(db, lexicon_id, term_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Term with ID {term_id} not found in lexicon '{lexicon_id}'"
            )
        
        # 204 No Content - no response body
        return None
    
    except HTTPException:
        raise
    
    except Exception as e:
        # Internal server error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete term: {str(e)}"
        )
