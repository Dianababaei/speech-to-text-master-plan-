"""
Post-processing service for transcription text.

This module applies domain-specific corrections using lexicon-based term replacements.
"""
import re
from typing import Optional
from sqlalchemy.orm import Session

from app.utils.logging import get_logger
from app.services.lexicon_service import load_lexicon_sync

logger = get_logger(__name__)


class PostProcessingError(Exception):
    """Base exception for post-processing errors."""
    pass


def apply_lexicon_corrections(text: str, lexicon: dict) -> str:
    """
    Apply lexicon-based term replacements to text.
    
    Performs case-insensitive whole-word replacements using the provided lexicon.
    
    Args:
        text: The text to process
        lexicon: Dictionary of {term: replacement} pairs
        
    Returns:
        Text with lexicon corrections applied
    """
    if not lexicon:
        return text
    
    processed_text = text
    
    # Apply each term replacement with word boundary matching (case-insensitive)
    for term, replacement in lexicon.items():
        # Use word boundaries to avoid partial matches
        # Use case-insensitive flag
        pattern = r'\b' + re.escape(term) + r'\b'
        processed_text = re.sub(pattern, replacement, processed_text, flags=re.IGNORECASE)
    
    return processed_text


def process_transcription(
    text: str,
    lexicon_id: Optional[str] = None,
    db: Optional[Session] = None
) -> str:
    """
    Apply post-processing to transcription text.
    
    Post-processing includes:
    - Lexicon-based corrections (domain-specific term fixes)
    - Preserving original language/script
    
    Args:
        text: Original transcription text
        lexicon_id: Optional lexicon ID for domain-specific processing
        db: Database session for loading lexicon terms
    
    Returns:
        Processed text
    
    Raises:
        PostProcessingError: If post-processing fails
    """
    try:
        logger.info(
            f"Starting post-processing. "
            f"Text length: {len(text)}, Lexicon ID: {lexicon_id}"
        )
        
        processed_text = text
        
        # Apply lexicon-based corrections if lexicon_id and db session provided
        if lexicon_id and db:
            try:
                # Load lexicon terms (from cache or database)
                lexicon = load_lexicon_sync(db, lexicon_id)
                
                if lexicon:
                    logger.info(f"Applying {len(lexicon)} lexicon corrections")
                    processed_text = apply_lexicon_corrections(processed_text, lexicon)
                else:
                    logger.info(f"No lexicon terms found for lexicon_id '{lexicon_id}', skipping corrections")
                    
            except Exception as e:
                logger.warning(f"Failed to load or apply lexicon '{lexicon_id}': {e}. Continuing without corrections.")
        else:
            if not lexicon_id:
                logger.info("No lexicon_id provided, skipping lexicon corrections")
            if not db:
                logger.info("No database session provided, skipping lexicon corrections")
        
        logger.info(
            f"Post-processing completed. "
            f"Processed length: {len(processed_text)}"
        )
        
        return processed_text
    
    except Exception as e:
        logger.error(f"Post-processing error: {str(e)}")
        raise PostProcessingError(f"Failed to process transcription: {str(e)}")
