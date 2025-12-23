"""
EXAMPLE: Lexicon CRUD Endpoints with Cache Invalidation

This is a reference implementation showing how to integrate cache invalidation
into lexicon CRUD endpoints (Task #26).

NOTE: This is an example file for reference. The actual CRUD endpoints should be
implemented in a separate task with proper schemas, validation, and error handling.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.database import get_db
from app.models.lexicon import LexiconTerm
from app.services.lexicon_service import invalidate_lexicon_cache

router = APIRouter(prefix="/lexicons", tags=["lexicons"])


# Example: Create a new term
@router.post("/{lexicon_id}/terms", status_code=status.HTTP_201_CREATED)
async def create_term(
    lexicon_id: str,
    term: str,
    replacement: str,
    db: Session = Depends(get_db)
):
    """
    Create a new lexicon term.
    
    After creating the term, invalidates the cache for this lexicon
    to ensure subsequent requests get the updated terms.
    """
    try:
        # Create new term in database
        new_term = LexiconTerm(
            id=uuid.uuid4(),
            lexicon_id=lexicon_id,
            term=term,
            replacement=replacement,
            is_active=True
        )
        db.add(new_term)
        db.commit()
        db.refresh(new_term)
        
        # Invalidate cache for this lexicon
        await invalidate_lexicon_cache(lexicon_id)
        
        return {
            "id": str(new_term.id),
            "lexicon_id": new_term.lexicon_id,
            "term": new_term.term,
            "replacement": new_term.replacement,
            "is_active": new_term.is_active
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create term: {str(e)}"
        )


# Example: Update a term
@router.put("/{lexicon_id}/terms/{term_id}")
async def update_term(
    lexicon_id: str,
    term_id: str,
    replacement: str = None,
    is_active: bool = None,
    db: Session = Depends(get_db)
):
    """
    Update an existing lexicon term.
    
    After updating, invalidates the cache to ensure changes are reflected.
    """
    try:
        # Find term
        term = db.query(LexiconTerm).filter(
            LexiconTerm.id == term_id,
            LexiconTerm.lexicon_id == lexicon_id
        ).first()
        
        if not term:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Term {term_id} not found in lexicon {lexicon_id}"
            )
        
        # Update fields
        if replacement is not None:
            term.replacement = replacement
        if is_active is not None:
            term.is_active = is_active
        
        db.commit()
        db.refresh(term)
        
        # Invalidate cache
        await invalidate_lexicon_cache(lexicon_id)
        
        return {
            "id": str(term.id),
            "lexicon_id": term.lexicon_id,
            "term": term.term,
            "replacement": term.replacement,
            "is_active": term.is_active
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update term: {str(e)}"
        )


# Example: Delete (soft delete) a term
@router.delete("/{lexicon_id}/terms/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_term(
    lexicon_id: str,
    term_id: str,
    db: Session = Depends(get_db)
):
    """
    Soft delete a lexicon term (sets is_active=False).
    
    After deletion, invalidates the cache.
    """
    try:
        # Find term
        term = db.query(LexiconTerm).filter(
            LexiconTerm.id == term_id,
            LexiconTerm.lexicon_id == lexicon_id
        ).first()
        
        if not term:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Term {term_id} not found in lexicon {lexicon_id}"
            )
        
        # Soft delete (set is_active=False)
        term.is_active = False
        db.commit()
        
        # Invalidate cache
        await invalidate_lexicon_cache(lexicon_id)
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete term: {str(e)}"
        )


# Example: Get all terms for a lexicon
@router.get("/{lexicon_id}/terms")
async def get_terms(
    lexicon_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all active terms for a lexicon.
    
    Note: This endpoint queries the database directly (not using cache)
    to provide administrative access to all terms with metadata.
    The cache is used for post-processing only.
    """
    terms = db.query(LexiconTerm).filter(
        LexiconTerm.lexicon_id == lexicon_id,
        LexiconTerm.is_active == True
    ).all()
    
    return [
        {
            "id": str(term.id),
            "lexicon_id": term.lexicon_id,
            "term": term.term,
            "replacement": term.replacement,
            "is_active": term.is_active,
            "created_at": term.created_at.isoformat(),
            "updated_at": term.updated_at.isoformat()
        }
        for term in terms
    ]
