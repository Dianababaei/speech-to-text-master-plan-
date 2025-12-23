"""
Post-processing service for transcription text.

This module applies domain-specific corrections using lexicon-based term replacements,
text cleanup, and numeral handling with comprehensive error handling and fallback strategies.
"""
import re
import traceback
from typing import Optional, Dict
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
        lexicon = load_lexicon_sync(lexicon_id, db)
        
        if not lexicon:
            logger.warning(f"No lexicon terms found for lexicon_id '{lexicon_id}', returning original text")
            return text
        
        # Apply corrections
        return apply_lexicon_corrections(text, lexicon)
        
    except Exception as e:
        logger.error(f"Failed to apply lexicon replacements for '{lexicon_id}': {str(e)}")
        raise PostProcessingError(f"Failed to apply lexicon replacements: {str(e)}")


def apply_text_cleanup(text: str) -> str:
    """
    Apply text cleanup and normalization.
    
    This function performs general text cleanup operations:
    - Normalize whitespace (multiple spaces, tabs, newlines)
    - Remove extra punctuation
    - Trim leading/trailing whitespace
    
    Args:
        text: The text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return text
    
    cleaned = text
    
    # Normalize whitespace: replace multiple spaces/tabs/newlines with single space
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Remove extra spaces around punctuation
    cleaned = re.sub(r'\s+([.,!?;:])', r'\1', cleaned)
    cleaned = re.sub(r'([.,!?;:])\s+', r'\1 ', cleaned)
    
    # Remove multiple consecutive punctuation marks (keep only one)
    cleaned = re.sub(r'([.,!?;:])\1+', r'\1', cleaned)
    
    # Trim leading and trailing whitespace
    cleaned = cleaned.strip()
    
    return cleaned


def apply_numeral_handling(text: str) -> str:
    """
    Apply numeral handling for Persian/English numerals.
    
    This function handles conversion between Persian and English numerals
    and ensures consistent numeral representation throughout the text.
    
    Persian numerals: ۰۱۲۳۴۵۶۷۸۹
    English numerals: 0123456789
    
    Currently converts Persian numerals to English for consistency.
    
    Args:
        text: The text to process
        
    Returns:
        Text with normalized numerals
    """
    if not text:
        return text
    
    # Persian to English numeral mapping
    persian_to_english = {
        '۰': '0',
        '۱': '1',
        '۲': '2',
        '۳': '3',
        '۴': '4',
        '۵': '5',
        '۶': '6',
        '۷': '7',
        '۸': '8',
        '۹': '9',
    }
    
    processed = text
    
    # Replace Persian numerals with English equivalents
    for persian, english in persian_to_english.items():
        processed = processed.replace(persian, english)
    
    return processed


class PostProcessingPipeline:
    """
    Orchestrates the complete post-processing pipeline for transcription text.
    
    The pipeline executes the following steps in sequence:
    1. Load lexicon terms from database/cache (if lexicon_id provided)
    2. Apply lexicon term replacements
    3. Apply text cleanup and normalization
    4. Apply numeral handling (Persian/English conversion)
    
    Each step can be individually enabled/disabled via configuration.
    """
    
    def __init__(
        self,
        enable_lexicon_replacement: bool = True,
        enable_text_cleanup: bool = True,
        enable_numeral_handling: bool = True
    ):
        """
        Initialize the pipeline with step configuration.
        
        Args:
            enable_lexicon_replacement: Enable lexicon-based term replacement
            enable_text_cleanup: Enable text cleanup and normalization
            enable_numeral_handling: Enable numeral handling
        """
        self.enable_lexicon_replacement = enable_lexicon_replacement
        self.enable_text_cleanup = enable_text_cleanup
        self.enable_numeral_handling = enable_numeral_handling
        
        self.logger = get_logger(__name__)
    
    def process(
        self,
        text: str,
        lexicon_id: Optional[str] = None,
        db: Optional[Session] = None,
        job_id: Optional[str] = None
    ) -> str:
        """
        Process transcription text through the complete pipeline.
        
        Args:
            text: Original transcription text from OpenAI
            lexicon_id: Optional lexicon ID for domain-specific processing
            db: Database session for loading lexicon terms
            job_id: Optional job ID for logging context
            
        Returns:
            Fully processed text
            
        Raises:
            PostProcessingError: If a critical error occurs during processing
        """
        from time import time
        
        pipeline_start = time()
        
        # Log pipeline entry
        log_context = {"job_id": job_id} if job_id else {}
        self.logger.info(
            f"Entering post-processing pipeline",
            extra={
                **log_context,
                "text_length": len(text),
                "word_count": len(text.split()),
                "lexicon_id": lexicon_id,
                "lexicon_enabled": self.enable_lexicon_replacement,
                "cleanup_enabled": self.enable_text_cleanup,
                "numeral_enabled": self.enable_numeral_handling,
            }
        )
        
        processed_text = text
        
        try:
            # Step 1: Apply lexicon replacements
            if self.enable_lexicon_replacement:
                step_start = time()
                
                if lexicon_id and db:
                    try:
                        lexicon = load_lexicon_sync(lexicon_id, db)
                        
                        if lexicon:
                            self.logger.debug(
                                f"Loaded {len(lexicon)} lexicon terms",
                                extra={**log_context, "lexicon_id": lexicon_id, "term_count": len(lexicon)}
                            )
                            
                            original_length = len(processed_text)
                            processed_text = apply_lexicon_corrections(processed_text, lexicon)
                            
                            step_duration = time() - step_start
                            self.logger.info(
                                f"Step 1: Lexicon replacement completed",
                                extra={
                                    **log_context,
                                    "step": "lexicon_replacement",
                                    "duration": round(step_duration, 3),
                                    "char_change": len(processed_text) - original_length,
                                    "word_count": len(processed_text.split()),
                                }
                            )
                        else:
                            self.logger.info(
                                f"Step 1: No lexicon terms found, skipping",
                                extra={**log_context, "lexicon_id": lexicon_id}
                            )
                    except Exception as e:
                        # Non-fatal error - log and continue
                        self.logger.warning(
                            f"Step 1: Lexicon replacement failed: {str(e)}",
                            extra={**log_context, "error_type": type(e).__name__}
                        )
                else:
                    self.logger.debug(
                        f"Step 1: Lexicon replacement skipped (no lexicon_id or db session)",
                        extra=log_context
                    )
            else:
                self.logger.debug(f"Step 1: Lexicon replacement disabled", extra=log_context)
            
            # Step 2: Apply text cleanup
            if self.enable_text_cleanup:
                step_start = time()
                
                original_length = len(processed_text)
                processed_text = apply_text_cleanup(processed_text)
                
                step_duration = time() - step_start
                self.logger.info(
                    f"Step 2: Text cleanup completed",
                    extra={
                        **log_context,
                        "step": "text_cleanup",
                        "duration": round(step_duration, 3),
                        "char_change": len(processed_text) - original_length,
                        "word_count": len(processed_text.split()),
                    }
                )
            else:
                self.logger.debug(f"Step 2: Text cleanup disabled", extra=log_context)
            
            # Step 3: Apply numeral handling
            if self.enable_numeral_handling:
                step_start = time()
                
                original_length = len(processed_text)
                processed_text = apply_numeral_handling(processed_text)
                
                step_duration = time() - step_start
                self.logger.info(
                    f"Step 3: Numeral handling completed",
                    extra={
                        **log_context,
                        "step": "numeral_handling",
                        "duration": round(step_duration, 3),
                        "char_change": len(processed_text) - original_length,
                        "word_count": len(processed_text.split()),
                    }
                )
            else:
                self.logger.debug(f"Step 3: Numeral handling disabled", extra=log_context)
            
            # Log pipeline exit
            pipeline_duration = time() - pipeline_start
            self.logger.info(
                f"Exiting post-processing pipeline",
                extra={
                    **log_context,
                    "total_duration": round(pipeline_duration, 3),
                    "original_length": len(text),
                    "processed_length": len(processed_text),
                    "original_words": len(text.split()),
                    "processed_words": len(processed_text.split()),
                }
            )
            
            return processed_text
            
        except Exception as e:
            pipeline_duration = time() - pipeline_start
            self.logger.error(
                f"Post-processing pipeline error: {str(e)}",
                extra={
                    **log_context,
                    "error_type": type(e).__name__,
                    "duration": round(pipeline_duration, 3),
                }
            )
            raise PostProcessingError(f"Pipeline processing failed: {str(e)}")


def create_pipeline(
    enable_lexicon_replacement: Optional[bool] = None,
    enable_text_cleanup: Optional[bool] = None,
    enable_numeral_handling: Optional[bool] = None
) -> PostProcessingPipeline:
    """
    Create a post-processing pipeline with configuration.
    
    If any parameter is None, the default from environment/config will be used.
    
    Args:
        enable_lexicon_replacement: Override for lexicon replacement step
        enable_text_cleanup: Override for text cleanup step
        enable_numeral_handling: Override for numeral handling step
        
    Returns:
        Configured PostProcessingPipeline instance
    """
    from app.config import (
        ENABLE_LEXICON_REPLACEMENT,
        ENABLE_TEXT_CLEANUP,
        ENABLE_NUMERAL_HANDLING
    )
    
    return PostProcessingPipeline(
        enable_lexicon_replacement=enable_lexicon_replacement if enable_lexicon_replacement is not None else ENABLE_LEXICON_REPLACEMENT,
        enable_text_cleanup=enable_text_cleanup if enable_text_cleanup is not None else ENABLE_TEXT_CLEANUP,
        enable_numeral_handling=enable_numeral_handling if enable_numeral_handling is not None else ENABLE_NUMERAL_HANDLING,
    )


def process_transcription(
    text: str,
    lexicon_id: Optional[str] = None,
    db: Optional[Session] = None,
    job_id: Optional[str] = None
) -> str:
    """
    Apply post-processing to transcription text with comprehensive error handling.
    
    This is a backward-compatible wrapper around the new pipeline.
    For new code, use create_pipeline() and call pipeline.process() directly.
    
    Post-processing includes:
    - Lexicon-based corrections (domain-specific term fixes)
    - Text cleanup and normalization
    - Numeral handling
    
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
