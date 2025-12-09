"""
Post-processing service for transcription text.

This module applies domain-specific corrections using lexicon-based term replacements,
text cleanup, and numeral handling with comprehensive error handling and fallback strategies.
"""
import re
import traceback
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


def apply_text_cleanup(text: str) -> str:
    """
    Apply basic text cleanup operations.
    
    This includes:
    - Removing extra whitespace
    - Normalizing line breaks
    - Removing trailing/leading whitespace
    
    Args:
        text: The text to clean up
        
    Returns:
        Cleaned text
    """
    if not text:
        return text
    
    # Normalize multiple spaces to single space
    cleaned_text = re.sub(r' +', ' ', text)
    
    # Normalize multiple line breaks to maximum of two
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    
    # Remove trailing/leading whitespace
    cleaned_text = cleaned_text.strip()
    
    return cleaned_text


def apply_numeral_handling(text: str) -> str:
    """
    Apply numeral normalization and formatting.
    
    This is a placeholder for future numeral processing logic such as:
    - Converting written numbers to digits
    - Formatting medical dosages
    - Standardizing units
    
    Args:
        text: The text to process
        
    Returns:
        Text with numeral handling applied
    """
    # Currently a pass-through - implement specific logic as needed
    return text


def process_transcription(
    text: str,
    lexicon_id: Optional[str] = None,
    db: Optional[Session] = None,
    job_id: Optional[str] = None
) -> str:
    """
    Apply post-processing to transcription text with comprehensive error handling.
    
    Post-processing pipeline includes (in order):
    1. Lexicon-based corrections (domain-specific term fixes)
    2. Text cleanup (whitespace normalization)
    3. Numeral handling (number formatting)
    
    Each step has independent error handling. If any step fails, the error is logged
    and processing continues with the output from the previous successful step.
    If all steps fail, returns the original input text.
    
    Args:
        text: Original transcription text
        lexicon_id: Optional lexicon ID for domain-specific processing
        db: Database session for loading lexicon terms
        job_id: Optional job ID for structured logging context
    
    Returns:
        Processed text (or original text if all processing fails)
    
    Note:
        This function never raises exceptions. All errors are logged and handled gracefully.
    """
    # Structured logging context
    log_context = {
        "job_id": job_id,
        "lexicon_id": lexicon_id,
        "text_length": len(text) if text else 0
    }
    
    logger.info(
        f"Starting post-processing pipeline. "
        f"Text length: {log_context['text_length']}, "
        f"Lexicon ID: {lexicon_id}, Job ID: {job_id}"
    )
    
    # Track which steps succeeded
    successful_steps = []
    failed_steps = []
    
    # Start with original text
    current_text = text
    
    # Step 1: Lexicon-based corrections
    if lexicon_id and db:
        try:
            logger.info(f"[Job {job_id}] Step 1: Loading lexicon '{lexicon_id}'")
            
            # Load lexicon terms (from cache or database)
            lexicon = load_lexicon_sync(db, lexicon_id)
            
            if lexicon:
                logger.info(
                    f"[Job {job_id}] Step 1: Applying {len(lexicon)} lexicon corrections"
                )
                
                # Apply corrections
                try:
                    corrected_text = apply_lexicon_corrections(current_text, lexicon)
                    current_text = corrected_text
                    successful_steps.append("lexicon_replacement")
                    
                    logger.info(
                        f"[Job {job_id}] Step 1: Lexicon corrections applied successfully"
                    )
                    
                except Exception as e:
                    error_msg = f"Lexicon replacement failed: {str(e)}"
                    logger.error(
                        f"[Job {job_id}] Step 1 ERROR: {error_msg}",
                        extra={
                            "job_id": job_id,
                            "lexicon_id": lexicon_id,
                            "step": "lexicon_replacement",
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "traceback": traceback.format_exc()
                        }
                    )
                    failed_steps.append("lexicon_replacement")
                    logger.warning(
                        f"[Job {job_id}] Step 1: Falling back to text before lexicon replacement"
                    )
                    # current_text remains unchanged (fallback to previous step)
            else:
                logger.info(
                    f"[Job {job_id}] Step 1: No lexicon terms found for '{lexicon_id}', "
                    f"skipping corrections"
                )
                successful_steps.append("lexicon_load_skipped")
                
        except Exception as e:
            error_msg = f"Lexicon loading failed: {str(e)}"
            logger.error(
                f"[Job {job_id}] Step 1 ERROR: {error_msg}",
                extra={
                    "job_id": job_id,
                    "lexicon_id": lexicon_id,
                    "step": "lexicon_load",
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "traceback": traceback.format_exc()
                }
            )
            failed_steps.append("lexicon_load")
            logger.warning(
                f"[Job {job_id}] Step 1: Proceeding without lexicon corrections"
            )
            # current_text remains unchanged (skip this step)
    else:
        if not lexicon_id:
            logger.info(f"[Job {job_id}] Step 1: No lexicon_id provided, skipping")
        if not db:
            logger.info(f"[Job {job_id}] Step 1: No database session provided, skipping")
        successful_steps.append("lexicon_skipped")
    
    # Step 2: Text cleanup
    try:
        logger.info(f"[Job {job_id}] Step 2: Applying text cleanup")
        
        cleaned_text = apply_text_cleanup(current_text)
        current_text = cleaned_text
        successful_steps.append("text_cleanup")
        
        logger.info(f"[Job {job_id}] Step 2: Text cleanup applied successfully")
        
    except Exception as e:
        error_msg = f"Text cleanup failed: {str(e)}"
        logger.error(
            f"[Job {job_id}] Step 2 ERROR: {error_msg}",
            extra={
                "job_id": job_id,
                "step": "text_cleanup",
                "error": str(e),
                "error_type": type(e).__name__,
                "text_length": len(current_text) if current_text else 0,
                "traceback": traceback.format_exc()
            }
        )
        failed_steps.append("text_cleanup")
        logger.warning(
            f"[Job {job_id}] Step 2: Falling back to text before cleanup"
        )
        # current_text remains unchanged (fallback to previous step)
    
    # Step 3: Numeral handling
    try:
        logger.info(f"[Job {job_id}] Step 3: Applying numeral handling")
        
        processed_numerals = apply_numeral_handling(current_text)
        current_text = processed_numerals
        successful_steps.append("numeral_handling")
        
        logger.info(f"[Job {job_id}] Step 3: Numeral handling applied successfully")
        
    except Exception as e:
        error_msg = f"Numeral handling failed: {str(e)}"
        logger.error(
            f"[Job {job_id}] Step 3 ERROR: {error_msg}",
            extra={
                "job_id": job_id,
                "step": "numeral_handling",
                "error": str(e),
                "error_type": type(e).__name__,
                "text_length": len(current_text) if current_text else 0,
                "traceback": traceback.format_exc()
            }
        )
        failed_steps.append("numeral_handling")
        logger.warning(
            f"[Job {job_id}] Step 3: Falling back to text before numeral handling"
        )
        # current_text remains unchanged (fallback to previous step)
    
    # Final result
    final_text = current_text if current_text else text
    
    # Summary logging
    if failed_steps:
        logger.warning(
            f"[Job {job_id}] Post-processing completed with failures. "
            f"Successful: {successful_steps}, Failed: {failed_steps}",
            extra={
                "job_id": job_id,
                "successful_steps": successful_steps,
                "failed_steps": failed_steps,
                "final_text_length": len(final_text) if final_text else 0
            }
        )
    else:
        logger.info(
            f"[Job {job_id}] Post-processing completed successfully. "
            f"All steps: {successful_steps}",
            extra={
                "job_id": job_id,
                "successful_steps": successful_steps,
                "final_text_length": len(final_text) if final_text else 0
            }
        )
    
    return final_text
