"""
Business logic for lexicon import/export operations.

Handles validation, database transactions, and data transformation
for lexicon term management.
"""

import logging
from typing import List, Dict, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import redis
from sqlalchemy import func

from app.models.lexicon_term import LexiconTerm
from app.schemas.lexicons import SkippedTerm

logger = logging.getLogger(__name__)


def validate_terms_for_import(
    lexicon_id: str,
    terms: List[Dict[str, str]],
    db: Session
) -> Tuple[List[Dict[str, str]], List[SkippedTerm]]:
    """
    Validate terms for import, checking for duplicates within the batch
    and conflicts with existing terms.
    
    Args:
        lexicon_id: The lexicon ID to import terms into
        terms: List of term dictionaries with 'term' and 'replacement' keys
        db: Database session
        
    Returns:
        Tuple of (valid_terms, skipped_terms)
        - valid_terms: List of terms that can be imported
        - skipped_terms: List of SkippedTerm objects with skip reasons
    """
    valid_terms = []
    skipped_terms = []
    seen_terms = {}  # Track terms seen in this batch (case-insensitive)
    
    # Get existing terms for this lexicon (case-insensitive lookup)
    existing_terms_query = db.query(LexiconTerm).filter(
        LexiconTerm.lexicon_id == lexicon_id,
        LexiconTerm.is_active == True
    ).all()
    
    # Create case-insensitive lookup of existing terms
    existing_terms_map = {
        term.term.lower(): term.term 
        for term in existing_terms_query
    }
    
    for term_data in terms:
        term = term_data['term']
        replacement = term_data['replacement']
        term_lower = term.lower()
        
        # Check for duplicate within import batch
        if term_lower in seen_terms:
            skipped_terms.append(SkippedTerm(
                term=term,
                replacement=replacement,
                reason=f"Duplicate term in import file (first occurrence at term: '{seen_terms[term_lower]}')"
            ))
            continue
        
        # Check for conflict with existing terms (case-insensitive)
        if term_lower in existing_terms_map:
            skipped_terms.append(SkippedTerm(
                term=term,
                replacement=replacement,
                reason=f"Term already exists in lexicon (existing term: '{existing_terms_map[term_lower]}')"
            ))
            continue
        
        # Term is valid
        seen_terms[term_lower] = term
        valid_terms.append(term_data)
    
    return valid_terms, skipped_terms


def import_terms_to_database(
    lexicon_id: str,
    terms: List[Dict[str, str]],
    db: Session
) -> int:
    """
    Import validated terms into the database using an atomic transaction.
    
    Args:
        lexicon_id: The lexicon ID to import terms into
        terms: List of validated term dictionaries
        db: Database session
        
    Returns:
        Number of terms successfully imported
        
    Raises:
        Exception: If database transaction fails (will rollback automatically)
    """
    try:
        # Create LexiconTerm objects
        lexicon_terms = []
        current_time = datetime.utcnow()
        
        for term_data in terms:
            lexicon_term = LexiconTerm(
                lexicon_id=lexicon_id,
                term=term_data['term'],
                replacement=term_data['replacement'],
                is_active=True,
                created_at=current_time,
                updated_at=current_time
            )
            lexicon_terms.append(lexicon_term)
        
        # Bulk insert all terms
        db.bulk_save_objects(lexicon_terms)
        db.commit()
        
        logger.info(f"Successfully imported {len(lexicon_terms)} terms to lexicon '{lexicon_id}'")
        return len(lexicon_terms)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to import terms to lexicon '{lexicon_id}': {str(e)}")
        raise


def export_terms_from_database(
    lexicon_id: str,
    db: Session
) -> List[Dict[str, str]]:
    """
    Export all active terms for a given lexicon from the database.
    
    Args:
        lexicon_id: The lexicon ID to export terms from
        db: Database session
        
    Returns:
        List of dictionaries with 'term' and 'replacement' keys
    """
    # Query all active terms for this lexicon
    terms = db.query(LexiconTerm).filter(
        LexiconTerm.lexicon_id == lexicon_id,
        LexiconTerm.is_active == True
    ).order_by(LexiconTerm.term).all()
    
    # Convert to list of dictionaries
    exported_terms = [
        {
            'term': term.term,
            'replacement': term.replacement
        }
        for term in terms
    ]
    
    logger.info(f"Exported {len(exported_terms)} terms from lexicon '{lexicon_id}'")
    return exported_terms
