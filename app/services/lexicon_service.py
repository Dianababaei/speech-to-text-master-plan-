"""
Lexicon Service

Business logic for managing lexicon terms.
"""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.lexicon import LexiconTerm
from app.schemas.lexicon import TermCreate, TermUpdate


def check_term_uniqueness(
    db: Session, 
    lexicon_id: str, 
    term: str, 
    exclude_id: Optional[int] = None
) -> bool:
    """
    Check if a term already exists in a lexicon (case-insensitive).
    
    Args:
        db: Database session
        lexicon_id: The lexicon identifier
        term: The term to check
        exclude_id: Optional term ID to exclude from check (for updates)
    
    Returns:
        bool: True if term exists, False otherwise
    """
    normalized = term.lower().strip()
    query = db.query(LexiconTerm).filter(
        LexiconTerm.lexicon_id == lexicon_id,
        LexiconTerm.normalized_term == normalized,
        LexiconTerm.is_active == True
    )
    
    if exclude_id:
        query = query.filter(LexiconTerm.id != exclude_id)
    
    return query.first() is not None


def create_term(
    db: Session, 
    lexicon_id: str, 
    term_data: TermCreate
) -> LexiconTerm:
    """
    Create a new lexicon term.
    
    Args:
        db: Database session
        lexicon_id: The lexicon identifier
        term_data: Term creation data
    
    Returns:
        LexiconTerm: The created term
    
    Raises:
        ValueError: If term already exists in the lexicon
    """
    # Check for duplicates
    if check_term_uniqueness(db, lexicon_id, term_data.term):
        raise ValueError(f"Term '{term_data.term}' already exists in lexicon '{lexicon_id}'")
    
    # Create normalized term for case-insensitive matching
    normalized_term = term_data.term.lower().strip()
    
    # Create new term
    new_term = LexiconTerm(
        lexicon_id=lexicon_id,
        term=term_data.term.strip(),
        normalized_term=normalized_term,
        replacement=term_data.replacement.strip(),
        is_active=True
    )
    
    db.add(new_term)
    db.commit()
    db.refresh(new_term)
    
    return new_term


def get_terms(
    db: Session, 
    lexicon_id: str, 
    page: int = 1, 
    limit: int = 50
) -> Tuple[List[LexiconTerm], int]:
    """
    Get paginated list of active terms in a lexicon.
    
    Args:
        db: Database session
        lexicon_id: The lexicon identifier
        page: Page number (1-indexed)
        limit: Items per page
    
    Returns:
        Tuple[List[LexiconTerm], int]: List of terms and total count
    """
    # Calculate offset
    offset = (page - 1) * limit
    
    # Query for active terms
    query = db.query(LexiconTerm).filter(
        LexiconTerm.lexicon_id == lexicon_id,
        LexiconTerm.is_active == True
    ).order_by(LexiconTerm.term)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    terms = query.offset(offset).limit(limit).all()
    
    return terms, total


def get_term_by_id(
    db: Session, 
    lexicon_id: str, 
    term_id: int
) -> Optional[LexiconTerm]:
    """
    Get a specific term by ID.
    
    Args:
        db: Database session
        lexicon_id: The lexicon identifier
        term_id: The term ID
    
    Returns:
        Optional[LexiconTerm]: The term if found, None otherwise
    """
    return db.query(LexiconTerm).filter(
        LexiconTerm.id == term_id,
        LexiconTerm.lexicon_id == lexicon_id
    ).first()


def update_term(
    db: Session, 
    lexicon_id: str, 
    term_id: int, 
    term_data: TermUpdate
) -> Optional[LexiconTerm]:
    """
    Update an existing lexicon term.
    
    Args:
        db: Database session
        lexicon_id: The lexicon identifier
        term_id: The term ID to update
        term_data: Updated term data
    
    Returns:
        Optional[LexiconTerm]: The updated term if found, None otherwise
    
    Raises:
        ValueError: If the updated term would create a duplicate
    """
    # Get existing term
    term = get_term_by_id(db, lexicon_id, term_id)
    if not term:
        return None
    
    # Check if the new term would create a duplicate
    if check_term_uniqueness(db, lexicon_id, term_data.term, exclude_id=term_id):
        raise ValueError(f"Term '{term_data.term}' already exists in lexicon '{lexicon_id}'")
    
    # Update fields
    term.term = term_data.term.strip()
    term.normalized_term = term_data.term.lower().strip()
    term.replacement = term_data.replacement.strip()
    # updated_at will be automatically updated by onupdate=func.now()
    
    db.commit()
    db.refresh(term)
    
    return term


def soft_delete_term(
    db: Session, 
    lexicon_id: str, 
    term_id: int
) -> bool:
    """
    Soft delete a term by setting is_active to False.
    
    Args:
        db: Database session
        lexicon_id: The lexicon identifier
        term_id: The term ID to delete
    
    Returns:
        bool: True if term was deleted, False if not found
    """
    term = get_term_by_id(db, lexicon_id, term_id)
    if not term:
        return False
    
    term.is_active = False
    # updated_at will be automatically updated by onupdate=func.now()
    
    db.commit()
    
    return True
