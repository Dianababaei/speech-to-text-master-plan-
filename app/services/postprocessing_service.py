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
                        lexicon = load_lexicon_sync(db, lexicon_id)
                        
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
    db: Optional[Session] = None
) -> str:
    """
    Apply post-processing to transcription text.
    
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
    
    Returns:
        Processed text
    
    Raises:
        PostProcessingError: If post-processing fails
    """
    pipeline = create_pipeline()
    return pipeline.process(text, lexicon_id=lexicon_id, db=db)
