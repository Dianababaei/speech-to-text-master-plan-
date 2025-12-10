"""
Text cleanup and normalization utilities for transcription output.

This module handles basic text quality improvements while preserving the 
original language, script, and transcription fidelity.
"""
import re
import unicodedata
from typing import Dict, Optional

from app.utils.logging import get_logger

logger = get_logger(__name__)


# Default configuration for cleanup operations
DEFAULT_CONFIG = {
    "normalize_whitespace": True,
    "normalize_persian_chars": True,
    "normalize_punctuation": True,
    "remove_artifacts": True,
    "normalize_line_breaks": True,
    "unicode_normalization": "NFC",  # NFC or NFKC
}


def normalize_whitespace(text: str, config: Dict) -> str:
    """
    Normalize whitespace in text.
    
    Operations:
    - Remove leading/trailing whitespace
    - Collapse multiple consecutive spaces to single space
    - Normalize line breaks if configured
    
    Args:
        text: Input text
        config: Configuration dictionary
        
    Returns:
        Text with normalized whitespace
    """
    if not config.get("normalize_whitespace", True):
        return text
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    # Normalize line breaks
    if config.get("normalize_line_breaks", True):
        # Convert various line break styles to single \n
        text = re.sub(r'\r\n|\r', '\n', text)
        # Collapse multiple consecutive line breaks to at most 2 (preserve paragraph breaks)
        text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Collapse multiple consecutive spaces to single space
    text = re.sub(r' {2,}', ' ', text)
    
    # Remove spaces at start/end of lines
    text = re.sub(r'^ +', '', text, flags=re.MULTILINE)
    text = re.sub(r' +$', '', text, flags=re.MULTILINE)
    
    return text


def normalize_persian_characters(text: str, config: Dict) -> str:
    """
    Normalize Persian character variants to standard forms.
    
    Normalizations:
    - Arabic ي (U+064A) -> Persian ی (U+06CC)
    - Arabic ك (U+0643) -> Persian ک (U+06A9)
    - Arabic ه variants to appropriate Persian forms
    
    Args:
        text: Input text
        config: Configuration dictionary
        
    Returns:
        Text with normalized Persian characters
    """
    if not config.get("normalize_persian_chars", True):
        return text
    
    # Normalize ي (Arabic Yeh) to ی (Persian Yeh/Farsi Yeh)
    text = text.replace('\u064A', '\u06CC')
    
    # Normalize ك (Arabic Kaf) to ک (Persian Kaf/Keheh)
    text = text.replace('\u0643', '\u06A9')
    
    # Normalize ى (Arabic Alef Maksura) to ی (Persian Yeh)
    text = text.replace('\u0649', '\u06CC')
    
    # Normalize Arabic Heh (ه U+0647) - keep as is, it's standard
    # Word-final forms are typically handled by Unicode normalization
    
    return text


def normalize_punctuation(text: str, config: Dict) -> str:
    """
    Normalize punctuation for consistency.
    
    Operations:
    - Normalize ellipsis: ... or …
    - Normalize dashes: -, –, —
    - Remove excessive punctuation
    
    Args:
        text: Input text
        config: Configuration dictionary
        
    Returns:
        Text with normalized punctuation
    """
    if not config.get("normalize_punctuation", True):
        return text
    
    # Normalize ellipsis character to three periods
    text = text.replace('…', '...')
    
    # Remove excessive ellipsis (4+ periods or multiple ellipsis)
    text = re.sub(r'\.{4,}', '...', text)
    text = re.sub(r'(\.{3}\s*){2,}', '... ', text)
    
    # Normalize various dashes to standard hyphen-minus for simple cases
    # Keep em-dash (—) for actual em-dash usage, normalize en-dash (–) to hyphen
    text = text.replace('–', '-')  # en-dash to hyphen
    
    # Remove excessive punctuation marks (???, !!!, etc.)
    text = re.sub(r'([!?]){3,}', r'\1\1', text)
    
    return text


def remove_transcription_artifacts(text: str, config: Dict) -> str:
    """
    Remove common transcription artifacts from services like OpenAI Whisper.
    
    Removes:
    - Timestamp markers: [00:00:00] or (00:00:00)
    - Sound markers: [Music], [Applause], [Laughter], etc.
    - Caption artifacts: [inaudible], [crosstalk], etc.
    
    Args:
        text: Input text
        config: Configuration dictionary
        
    Returns:
        Text with artifacts removed
    """
    if not config.get("remove_artifacts", True):
        return text
    
    # Remove timestamp markers like [00:00:00] or (00:00:00)
    text = re.sub(r'\[?\d{1,2}:\d{2}:\d{2}\]?', '', text)
    text = re.sub(r'\[?\d{1,2}:\d{2}\]?', '', text)
    
    # Remove common sound/event markers (case-insensitive)
    artifacts = [
        r'\[Music\]',
        r'\[Applause\]',
        r'\[Laughter\]',
        r'\[Silence\]',
        r'\[Background noise\]',
        r'\[Noise\]',
        r'\[Sound\]',
        r'\[Audio\]',
        r'\[Inaudible\]',
        r'\[Crosstalk\]',
        r'\[Phone ringing\]',
        r'\[Door closing\]',
        r'\[Clears throat\]',
        r'♪.*?♪',  # Musical notes surrounding text
    ]
    
    for artifact in artifacts:
        text = re.sub(artifact, '', text, flags=re.IGNORECASE)
    
    # Remove generic bracketed markers like [something]
    # But be conservative - only remove if it looks like an artifact
    text = re.sub(r'\[\s*\w+\s*\]', '', text)
    
    return text


def apply_unicode_normalization(text: str, config: Dict) -> str:
    """
    Apply Unicode normalization to text.
    
    Args:
        text: Input text
        config: Configuration dictionary (uses 'unicode_normalization' key)
        
    Returns:
        Unicode-normalized text
    """
    normalization_form = config.get("unicode_normalization", "NFC")
    
    if normalization_form not in ("NFC", "NFKC", "NFD", "NFKD", None):
        logger.warning(f"Invalid unicode_normalization form '{normalization_form}', using NFC")
        normalization_form = "NFC"
    
    if normalization_form and normalization_form != "None":
        text = unicodedata.normalize(normalization_form, text)
    
    return text


def cleanup_text(text: str, config: Optional[Dict] = None) -> str:
    """
    Apply comprehensive text cleanup and normalization.
    
    This function applies multiple cleanup operations while preserving:
    - Original language (no translation)
    - Original script (no transliteration)
    - Transcription fidelity (minimal changes)
    
    Operations performed (configurable):
    1. Whitespace normalization
    2. Persian character normalization
    3. Punctuation consistency
    4. Transcription artifact removal
    5. Unicode normalization
    
    Args:
        text: Input text to clean
        config: Optional configuration dictionary. Keys:
            - normalize_whitespace (bool): Enable whitespace normalization (default: True)
            - normalize_persian_chars (bool): Enable Persian char normalization (default: True)
            - normalize_punctuation (bool): Enable punctuation normalization (default: True)
            - remove_artifacts (bool): Enable artifact removal (default: True)
            - normalize_line_breaks (bool): Enable line break normalization (default: True)
            - unicode_normalization (str): Unicode form - "NFC", "NFKC", or None (default: "NFC")
    
    Returns:
        Cleaned and normalized text
        
    Example:
        >>> text = "  Hello   world  [Music]  "
        >>> cleanup_text(text)
        'Hello world'
        
        >>> text = "سلام   دنيا"  # With Arabic ي
        >>> cleanup_text(text)
        'سلام دنیا'  # With Persian ی
    """
    if not text:
        return text
    
    # Merge config with defaults
    effective_config = DEFAULT_CONFIG.copy()
    if config:
        effective_config.update(config)
    
    original_length = len(text)
    logger.debug(f"Starting text cleanup. Original length: {original_length}")
    
    # Apply cleanup operations in sequence
    text = normalize_whitespace(text, effective_config)
    text = normalize_persian_characters(text, effective_config)
    text = normalize_punctuation(text, effective_config)
    text = remove_transcription_artifacts(text, effective_config)
    text = apply_unicode_normalization(text, effective_config)
    
    # Final whitespace cleanup after all operations
    text = text.strip()
    
    cleaned_length = len(text)
    chars_removed = original_length - cleaned_length
    
    if chars_removed > 0:
        logger.info(
            f"Text cleanup completed. "
            f"Original: {original_length} chars, "
            f"Cleaned: {cleaned_length} chars, "
            f"Removed: {chars_removed} chars"
        )
    else:
        logger.debug("Text cleanup completed with no changes")
    
    return text
