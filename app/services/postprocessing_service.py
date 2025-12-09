"""
Post-processing service for transcription text.

This module applies domain-specific corrections using lexicon-based term replacements.
Implements advanced features like case preservation, longest-match-first, and Unicode handling.
"""
import re
from typing import Optional, Dict, Tuple, List
from sqlalchemy.orm import Session

from app.utils.logging import get_logger
from app.services.lexicon_service import load_lexicon_sync

logger = get_logger(__name__)


class PostProcessingError(Exception):
    """Base exception for post-processing errors."""
    pass


def _preserve_case(original: str, replacement: str) -> str:
    """
    Preserve the case pattern of the original text when applying replacement.
    
    Implements smart case preservation:
    - If original is all uppercase, return replacement in uppercase
    - If original is title case (first letter uppercase), return replacement in title case
    - If original is all lowercase, return replacement as-is (from lexicon)
    - Otherwise, return replacement as-is
    
    Args:
        original: The original matched text from the transcription
        replacement: The replacement text from the lexicon
        
    Returns:
        Replacement text with case pattern preserved
        
    Examples:
        >>> _preserve_case("MRI", "mri")
        "MRI"
        >>> _preserve_case("Mri", "mri")
        "Mri"
        >>> _preserve_case("mri", "MRI")
        "MRI"
    """
    if not original or not replacement:
        return replacement
    
    if original.isupper():
        return replacement.upper()
    elif len(original) > 1 and original[0].isupper() and original[1:].islower():
        # Title case: capitalize first letter
        return replacement[0].upper() + replacement[1:] if len(replacement) > 0 else replacement
    elif len(original) == 1 and original[0].isupper():
        # Single uppercase letter
        return replacement[0].upper() + replacement[1:] if len(replacement) > 0 else replacement
    else:
        # Keep replacement as-is from lexicon
        return replacement


def apply_lexicon_corrections(text: str, lexicon: Dict[str, str]) -> str:
    """
    Apply lexicon-based term replacements to text with advanced features.
    
    Features:
    - Case-insensitive matching with case preservation
    - Longest-match-first to prefer longer terms
    - Whole-word matching with word boundaries
    - Unicode-safe for Persian/English mixed text
    - Comprehensive logging for debugging
    
    Args:
        text: The text to process
        lexicon: Dictionary of {term: replacement} pairs
        
    Returns:
        Text with lexicon corrections applied
        
    Raises:
        PostProcessingError: If replacement fails
    """
    if not lexicon:
        logger.debug("Empty lexicon provided, returning original text")
        return text
    
    try:
        # Sort terms by length (longest first) for longest-match-first strategy
        sorted_terms = sorted(lexicon.items(), key=lambda x: len(x[0]), reverse=True)
        logger.debug(f"Processing {len(sorted_terms)} lexicon terms (longest-match-first)")
        
        processed_text = text
        replacements_made = 0
        replacement_log = []
        
        # Apply each term replacement with word boundary matching (case-insensitive)
        for term, replacement in sorted_terms:
            # Use word boundaries to prefer whole-word matches
            # \b doesn't work well with Unicode, so we use a more flexible pattern
            # that handles Persian/English boundaries
            pattern = r'(?<!\w)' + re.escape(term) + r'(?!\w)'
            
            # Find all matches to log them
            matches = list(re.finditer(pattern, processed_text, flags=re.IGNORECASE | re.UNICODE))
            
            if matches:
                # Apply replacement with case preservation
                def replace_with_case_preservation(match):
                    original = match.group(0)
                    preserved_replacement = _preserve_case(original, replacement)
                    return preserved_replacement
                
                processed_text = re.sub(
                    pattern, 
                    replace_with_case_preservation, 
                    processed_text, 
                    flags=re.IGNORECASE | re.UNICODE
                )
                
                replacements_made += len(matches)
                replacement_log.append({
                    'term': term,
                    'replacement': replacement,
                    'count': len(matches),
                    'positions': [match.span() for match in matches]
                })
                
                logger.debug(
                    f"Replaced '{term}' → '{replacement}' "
                    f"({len(matches)} occurrence{'s' if len(matches) > 1 else ''})"
                )
        
        # Log summary
        if replacements_made > 0:
            logger.info(
                f"Applied {replacements_made} lexicon correction(s) "
                f"from {len([r for r in replacement_log if r['count'] > 0])} unique term(s)"
            )
            logger.debug(f"Replacement details: {replacement_log}")
        else:
            logger.debug("No lexicon corrections applied (no matches found)")
        
        return processed_text
        
    except Exception as e:
        logger.error(f"Error applying lexicon corrections: {str(e)}")
        raise PostProcessingError(f"Failed to apply lexicon corrections: {str(e)}")


def apply_lexicon_replacements(text: str, lexicon_id: str, db: Session) -> str:
    """
    Apply lexicon replacements to text by loading the specified lexicon.
    
    This is a convenience function that combines lexicon loading and text processing.
    Matches the function signature specified in technical requirements.
    
    Args:
        text: The text to process
        lexicon_id: The lexicon identifier to load and apply
        db: Database session for loading lexicon terms
        
    Returns:
        Text with lexicon replacements applied
        
    Raises:
        PostProcessingError: If lexicon loading or processing fails
    """
    try:
        logger.info(f"Applying lexicon replacements for lexicon_id: '{lexicon_id}'")
        
        # Load lexicon terms (from cache or database)
        lexicon = load_lexicon_sync(db, lexicon_id)
        
        if not lexicon:
            logger.warning(f"No lexicon terms found for lexicon_id '{lexicon_id}', returning original text")
            return text
        
        # Apply corrections
        return apply_lexicon_corrections(text, lexicon)
        
    except Exception as e:
        logger.error(f"Failed to apply lexicon replacements for '{lexicon_id}': {str(e)}")
        raise PostProcessingError(f"Failed to apply lexicon replacements: {str(e)}")


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
                # Use the new apply_lexicon_replacements function
                processed_text = apply_lexicon_replacements(text, lexicon_id, db)
                    
            except Exception as e:
                logger.warning(f"Failed to apply lexicon '{lexicon_id}': {e}. Continuing without corrections.")
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
