"""
Numeral Handler Service

This module provides numeral handling logic for Persian and English numerals
in transcription text. It ensures consistent numeral formatting based on
configuration or domain-specific conventions, particularly important for
medical terminology.

Features:
- Persian ↔ English numeral conversion
- Medical term preservation (vertebral levels, measurements, medical codes)
- Strategy-based processing (english/persian/preserve/context_aware)
- Lexicon-specific numeral preferences
"""

import re
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.utils.logging import get_logger

logger = get_logger(__name__)

# Numeral mappings
PERSIAN_TO_ENGLISH = {
    '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
    '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
}

ENGLISH_TO_PERSIAN = {
    '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
    '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
}

# Medical term patterns that should preserve English numerals
MEDICAL_CODE_PATTERNS = [
    # Vertebral levels: T1-T12, L1-L5, C1-C7, S1-S5
    r'\b[TLCS]\d+(?:-[TLCS]?\d+)?\b',
    # Measurements with units: 10mg, 5cm, 3.5mm, 2.5kg
    r'\b\d+(?:\.\d+)?(?:mg|g|kg|ml|l|cm|mm|m)\b',
    # Medical codes with numbers: ICD codes, etc.
    r'\b[A-Z]\d+(?:\.\d+)?\b',
]

# Compile medical patterns for efficiency
COMPILED_MEDICAL_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in MEDICAL_CODE_PATTERNS]


def persian_to_english(text: str) -> str:
    """
    Convert Persian numerals to English numerals.
    
    Args:
        text: Text containing Persian numerals
        
    Returns:
        Text with Persian numerals converted to English
    """
    for persian, english in PERSIAN_TO_ENGLISH.items():
        text = text.replace(persian, english)
    return text


def english_to_persian(text: str) -> str:
    """
    Convert English numerals to Persian numerals.
    
    Args:
        text: Text containing English numerals
        
    Returns:
        Text with English numerals converted to Persian
    """
    for english, persian in ENGLISH_TO_PERSIAN.items():
        text = text.replace(english, persian)
    return text


def detect_medical_terms(text: str) -> list:
    """
    Detect medical terms with numerals that should be preserved.
    
    Args:
        text: Text to scan for medical terms
        
    Returns:
        List of (start, end, matched_text) tuples for medical terms
    """
    medical_terms = []
    
    for pattern in COMPILED_MEDICAL_PATTERNS:
        for match in pattern.finditer(text):
            medical_terms.append((match.start(), match.end(), match.group()))
    
    # Sort by position
    medical_terms.sort(key=lambda x: x[0])
    
    return medical_terms


def is_position_in_medical_term(position: int, medical_terms: list) -> bool:
    """
    Check if a position in text is within a medical term.
    
    Args:
        position: Character position in text
        medical_terms: List of (start, end, text) tuples
        
    Returns:
        True if position is within any medical term
    """
    for start, end, _ in medical_terms:
        if start <= position < end:
            return True
    return False


def convert_numerals_with_preservation(text: str, converter_func, medical_terms: list) -> str:
    """
    Convert numerals while preserving medical terms.
    
    Args:
        text: Text to convert
        converter_func: Function to convert numerals (persian_to_english or english_to_persian)
        medical_terms: List of (start, end, text) tuples for medical terms to preserve
        
    Returns:
        Text with numerals converted except in medical terms
    """
    if not medical_terms:
        # No medical terms to preserve, convert everything
        return converter_func(text)
    
    # Build result by processing segments
    result = []
    last_end = 0
    
    for start, end, term_text in medical_terms:
        # Convert text before medical term
        if start > last_end:
            segment = text[last_end:start]
            result.append(converter_func(segment))
        
        # Preserve medical term as-is
        result.append(term_text)
        last_end = end
    
    # Convert remaining text after last medical term
    if last_end < len(text):
        segment = text[last_end:]
        result.append(converter_func(segment))
    
    return ''.join(result)


def apply_english_strategy(text: str) -> Tuple[str, int]:
    """
    Apply English numeral strategy: Convert all to English (0-9).
    
    Args:
        text: Text to process
        
    Returns:
        Tuple of (processed_text, conversion_count)
    """
    # Count Persian numerals before conversion
    persian_count = sum(1 for char in text if char in PERSIAN_TO_ENGLISH)
    
    processed_text = persian_to_english(text)
    
    return processed_text, persian_count


def apply_persian_strategy(text: str) -> Tuple[str, int]:
    """
    Apply Persian numeral strategy: Convert all to Persian (۰-۹).
    
    Args:
        text: Text to process
        
    Returns:
        Tuple of (processed_text, conversion_count)
    """
    # Count English numerals before conversion
    english_count = sum(1 for char in text if char in ENGLISH_TO_PERSIAN)
    
    processed_text = english_to_persian(text)
    
    return processed_text, english_count


def apply_context_aware_strategy(text: str) -> Tuple[str, int]:
    """
    Apply context-aware strategy: Medical codes in English, standalone numbers in Persian.
    
    This strategy:
    1. Detects medical terms (vertebral levels, measurements, medical codes)
    2. Keeps medical terms in English numerals
    3. Converts standalone numbers to Persian numerals
    
    Args:
        text: Text to process
        
    Returns:
        Tuple of (processed_text, conversion_count)
    """
    # First, detect all medical terms in the text
    medical_terms = detect_medical_terms(text)
    
    logger.debug(f"Detected {len(medical_terms)} medical terms to preserve: {[term[2] for term in medical_terms]}")
    
    # Convert medical terms to English numerals (if they have Persian numerals)
    # This ensures medical terms always use English numerals
    processed_text = text
    conversion_count = 0
    
    if medical_terms:
        # Build result preserving medical terms with English numerals
        result = []
        last_end = 0
        
        for start, end, term_text in medical_terms:
            # Convert non-medical text before this term to Persian
            if start > last_end:
                segment = text[last_end:start]
                converted_segment = english_to_persian(segment)
                conversion_count += sum(1 for c in segment if c in ENGLISH_TO_PERSIAN)
                result.append(converted_segment)
            
            # Ensure medical term uses English numerals
            english_term = persian_to_english(term_text)
            result.append(english_term)
            last_end = end
        
        # Convert remaining text after last medical term to Persian
        if last_end < len(text):
            segment = text[last_end:]
            converted_segment = english_to_persian(segment)
            conversion_count += sum(1 for c in segment if c in ENGLISH_TO_PERSIAN)
            result.append(converted_segment)
        
        processed_text = ''.join(result)
    else:
        # No medical terms, convert all to Persian
        processed_text = english_to_persian(text)
        conversion_count = sum(1 for char in text if char in ENGLISH_TO_PERSIAN)
    
    return processed_text, conversion_count


def get_lexicon_numeral_strategy(db: Optional[Session], lexicon_id: Optional[str]) -> Optional[str]:
    """
    Get numeral strategy from lexicon metadata.
    
    Args:
        db: Database session
        lexicon_id: Lexicon identifier
        
    Returns:
        Numeral strategy from lexicon metadata, or None if not specified
    """
    if not db or not lexicon_id:
        return None
    
    try:
        from app.models.lexicon import LexiconTerm
        from sqlalchemy import and_
        
        # Query one term from this lexicon to get metadata
        term = db.query(LexiconTerm).filter(
            and_(
                LexiconTerm.lexicon_id == lexicon_id,
                LexiconTerm.is_active == True
            )
        ).first()
        
        if term and term.metadata and isinstance(term.metadata, dict):
            numeral_strategy = term.metadata.get('numeral_strategy')
            if numeral_strategy:
                logger.info(f"Lexicon '{lexicon_id}' specifies numeral strategy: '{numeral_strategy}'")
                return numeral_strategy
        
    except Exception as e:
        logger.warning(f"Error retrieving numeral strategy from lexicon '{lexicon_id}': {e}")
    
    return None


def process_numerals(
    text: str,
    strategy: str = "english",
    lexicon_id: Optional[str] = None,
    db: Optional[Session] = None
) -> str:
    """
    Process numerals in text based on specified strategy.
    
    This is the main entry point for numeral processing. It applies
    different conversion strategies based on configuration and lexicon
    preferences.
    
    Strategy options:
    - "english": Convert all numerals to English (0-9)
    - "persian": Convert all numerals to Persian (۰-۹)
    - "preserve": Keep original numerals (no conversion)
    - "context_aware": Medical codes in English, standalone numbers in Persian
    
    Args:
        text: Text to process
        strategy: Numeral conversion strategy (default: "english")
        lexicon_id: Optional lexicon ID for domain-specific preferences
        db: Optional database session for loading lexicon metadata
        
    Returns:
        Processed text with numerals converted according to strategy
        
    Raises:
        ValueError: If strategy is invalid
    """
    if not text:
        return text
    
    # Check for lexicon-specific strategy override
    lexicon_strategy = get_lexicon_numeral_strategy(db, lexicon_id)
    if lexicon_strategy:
        strategy = lexicon_strategy
    
    logger.info(
        f"Processing numerals with strategy '{strategy}'. "
        f"Text length: {len(text)}, Lexicon ID: {lexicon_id}"
    )
    
    # Validate strategy
    valid_strategies = ["english", "persian", "preserve", "context_aware"]
    if strategy not in valid_strategies:
        logger.error(f"Invalid numeral strategy '{strategy}'. Valid options: {valid_strategies}")
        raise ValueError(f"Invalid numeral strategy '{strategy}'. Must be one of: {', '.join(valid_strategies)}")
    
    # Apply strategy
    processed_text = text
    conversion_count = 0
    
    try:
        if strategy == "preserve":
            logger.info("Strategy 'preserve': No numeral conversion applied")
            return text
        
        elif strategy == "english":
            processed_text, conversion_count = apply_english_strategy(text)
            logger.info(f"Strategy 'english': Converted {conversion_count} Persian numerals to English")
        
        elif strategy == "persian":
            processed_text, conversion_count = apply_persian_strategy(text)
            logger.info(f"Strategy 'persian': Converted {conversion_count} English numerals to Persian")
        
        elif strategy == "context_aware":
            processed_text, conversion_count = apply_context_aware_strategy(text)
            logger.info(
                f"Strategy 'context_aware': Applied context-aware conversion. "
                f"Conversions: {conversion_count}"
            )
        
        # Log if text changed
        if processed_text != text:
            logger.debug(f"Numeral conversion resulted in text changes (length: {len(text)} -> {len(processed_text)})")
        else:
            logger.debug("No numeral changes after processing")
        
        return processed_text
    
    except Exception as e:
        logger.error(f"Error processing numerals with strategy '{strategy}': {e}")
        # Return original text on error
        return text
