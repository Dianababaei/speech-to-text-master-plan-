"""
Lexicon Validation Service

This module provides comprehensive validation and conflict detection logic for lexicon terms
to ensure data integrity and prevent operational issues during transcription post-processing.

Validation Rules:
- Term Uniqueness: No duplicate terms within same lexicon_id (case-insensitive)
- Format Validation: No empty strings, whitespace-only, or exceeding length limits
- Circular Replacement Detection: Identify chains where term A → term B → term A
- Conflict Detection: Identify overlapping patterns (e.g., "MRI scan" vs "MRI")
"""

import logging
from typing import List, Dict, Optional, Set, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.models.lexicon import LexiconTerm

logger = logging.getLogger(__name__)

# Validation constants
MIN_TERM_LENGTH = 1
MAX_TERM_LENGTH = 200
MIN_REPLACEMENT_LENGTH = 1
MAX_REPLACEMENT_LENGTH = 500


class ValidationError:
    """Represents a single validation error."""
    
    def __init__(self, field: str, issue: str, value: Optional[str] = None, **kwargs):
        """
        Initialize a validation error.
        
        Args:
            field: The field that failed validation (e.g., "term", "replacement")
            issue: The type of issue (e.g., "duplicate", "circular_reference", "too_long")
            value: The problematic value
            **kwargs: Additional context (e.g., chain for circular references)
        """
        self.field = field
        self.issue = issue
        self.value = value
        self.context = kwargs
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API response."""
        result = {
            "field": self.field,
            "issue": self.issue
        }
        if self.value is not None:
            result["value"] = self.value
        result.update(self.context)
        return result


class ValidationResult:
    """Result of validation with errors and warnings."""
    
    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
    
    def add_error(self, field: str, issue: str, value: Optional[str] = None, **kwargs):
        """Add a validation error."""
        self.errors.append(ValidationError(field, issue, value, **kwargs))
    
    def add_warning(self, field: str, issue: str, value: Optional[str] = None, **kwargs):
        """Add a validation warning."""
        self.warnings.append(ValidationError(field, issue, value, **kwargs))
    
    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are warnings."""
        return len(self.warnings) > 0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API response."""
        result = {
            "valid": self.is_valid,
            "errors": [e.to_dict() for e in self.errors]
        }
        if self.warnings:
            result["warnings"] = [w.to_dict() for w in self.warnings]
        return result
    
    def to_error_detail(self, message: str = "Term validation failed") -> Dict:
        """Convert to FastAPI HTTPException detail format."""
        return {
            "error_type": "validation_error",
            "message": message,
            "errors": [e.to_dict() for e in self.errors]
        }


def validate_format(term: str, replacement: str) -> ValidationResult:
    """
    Validate term and replacement format.
    
    Checks for:
    - Empty strings or whitespace-only values
    - Length limits
    - Null values (handled by Pydantic, but double-check)
    
    Args:
        term: The term to validate
        replacement: The replacement to validate
    
    Returns:
        ValidationResult with any format errors
    """
    result = ValidationResult()
    
    # Check term
    if not term or not term.strip():
        result.add_error("term", "empty_or_whitespace", term)
    elif len(term.strip()) < MIN_TERM_LENGTH:
        result.add_error("term", "too_short", term, min_length=MIN_TERM_LENGTH)
    elif len(term.strip()) > MAX_TERM_LENGTH:
        result.add_error("term", "too_long", term, max_length=MAX_TERM_LENGTH, actual_length=len(term.strip()))
    
    # Check for excessive whitespace
    if term and term != term.strip():
        result.add_warning("term", "leading_or_trailing_whitespace", term)
    
    # Check replacement
    if not replacement or not replacement.strip():
        result.add_error("replacement", "empty_or_whitespace", replacement)
    elif len(replacement.strip()) < MIN_REPLACEMENT_LENGTH:
        result.add_error("replacement", "too_short", replacement, min_length=MIN_REPLACEMENT_LENGTH)
    elif len(replacement.strip()) > MAX_REPLACEMENT_LENGTH:
        result.add_error("replacement", "too_long", replacement, 
                        max_length=MAX_REPLACEMENT_LENGTH, actual_length=len(replacement.strip()))
    
    # Check for excessive whitespace
    if replacement and replacement != replacement.strip():
        result.add_warning("replacement", "leading_or_trailing_whitespace", replacement)
    
    return result


def validate_uniqueness(
    db: Session,
    lexicon_id: str,
    term: str,
    exclude_term_id: Optional[int] = None
) -> ValidationResult:
    """
    Validate term uniqueness within a lexicon (case-insensitive).
    
    Args:
        db: Database session
        lexicon_id: The lexicon identifier
        term: The term to check
        exclude_term_id: Optional term ID to exclude (for updates)
    
    Returns:
        ValidationResult with uniqueness errors if duplicate found
    """
    result = ValidationResult()
    
    if not term or not term.strip():
        # Format validation will catch this
        return result
    
    normalized_term = term.lower().strip()
    
    # Query for existing term
    query = db.query(LexiconTerm).filter(
        LexiconTerm.lexicon_id == lexicon_id,
        LexiconTerm.normalized_term == normalized_term,
        LexiconTerm.is_active == True
    )
    
    if exclude_term_id:
        query = query.filter(LexiconTerm.id != exclude_term_id)
    
    existing_term = query.first()
    
    if existing_term:
        result.add_error(
            "term",
            "duplicate",
            term,
            existing_term_id=existing_term.id,
            existing_term=existing_term.term,
            message=f"Term '{term}' already exists in lexicon '{lexicon_id}'"
        )
    
    return result


def detect_circular_replacements(
    db: Session,
    lexicon_id: str,
    term: str,
    replacement: str,
    exclude_term_id: Optional[int] = None
) -> ValidationResult:
    """
    Detect circular replacement chains.
    
    A circular chain exists when:
    - A → B and B → A (direct cycle)
    - A → B → C → A (longer cycle)
    
    Args:
        db: Database session
        lexicon_id: The lexicon identifier
        term: The term being validated
        replacement: The replacement for the term
        exclude_term_id: Optional term ID to exclude (for updates)
    
    Returns:
        ValidationResult with circular reference errors if cycle detected
    """
    result = ValidationResult()
    
    if not term or not replacement:
        return result
    
    # Normalize for comparison
    normalized_term = term.lower().strip()
    normalized_replacement = replacement.lower().strip()
    
    # Quick check: term and replacement are the same (self-reference)
    if normalized_term == normalized_replacement:
        result.add_error(
            "replacement",
            "self_reference",
            replacement,
            chain=[term, replacement],
            message=f"Term and replacement cannot be identical: '{term}'"
        )
        return result
    
    # Build a map of all active terms and their replacements in this lexicon
    query = db.query(LexiconTerm).filter(
        LexiconTerm.lexicon_id == lexicon_id,
        LexiconTerm.is_active == True
    )
    
    if exclude_term_id:
        query = query.filter(LexiconTerm.id != exclude_term_id)
    
    all_terms = query.all()
    
    # Create replacement graph: term -> replacement (normalized)
    replacement_graph: Dict[str, str] = {}
    for t in all_terms:
        replacement_graph[t.normalized_term] = t.replacement.lower().strip()
    
    # Add the term being validated to the graph
    replacement_graph[normalized_term] = normalized_replacement
    
    # Detect cycles using DFS
    def find_cycle(start: str, current: str, path: List[str], visited: Set[str]) -> Optional[List[str]]:
        """
        Find a cycle starting from 'start' node.
        
        Args:
            start: The starting node
            current: Current node in traversal
            path: Current path taken
            visited: Set of visited nodes in current path
        
        Returns:
            The cycle path if found, None otherwise
        """
        if current in visited:
            # Found a cycle
            if current == start:
                return path + [current]
            return None
        
        if current not in replacement_graph:
            # Dead end, no replacement for this term
            return None
        
        next_node = replacement_graph[current]
        
        # Check if next node creates a cycle back to start
        if next_node == start:
            return path + [current, next_node]
        
        # Continue searching
        visited.add(current)
        cycle = find_cycle(start, next_node, path + [current], visited.copy())
        
        return cycle
    
    # Check for cycle starting from our new term
    cycle = find_cycle(normalized_term, normalized_term, [], set())
    
    if cycle:
        # Convert back to original case for display
        display_chain = []
        for normalized in cycle:
            # Find original term for display
            original = None
            if normalized == normalized_term:
                original = term
            elif normalized == normalized_replacement:
                original = replacement
            else:
                for t in all_terms:
                    if t.normalized_term == normalized:
                        original = t.term
                        break
                    if t.replacement.lower().strip() == normalized:
                        original = t.replacement
                        break
            
            if original:
                display_chain.append(original)
            else:
                display_chain.append(normalized)
        
        result.add_error(
            "replacement",
            "circular_reference",
            replacement,
            chain=display_chain,
            message=f"Circular replacement detected: {' → '.join(display_chain)}"
        )
    
    return result


def detect_conflicts(
    db: Session,
    lexicon_id: str,
    term: str,
    exclude_term_id: Optional[int] = None
) -> ValidationResult:
    """
    Detect overlapping/conflicting terms within a lexicon.
    
    Conflicts occur when:
    - One term is a substring of another (e.g., "MRI" and "MRI scan")
    - Terms overlap in a way that could cause ambiguous matches
    
    Args:
        db: Database session
        lexicon_id: The lexicon identifier
        term: The term being validated
        exclude_term_id: Optional term ID to exclude (for updates)
    
    Returns:
        ValidationResult with conflict warnings
    """
    result = ValidationResult()
    
    if not term or not term.strip():
        return result
    
    normalized_term = term.lower().strip()
    
    # Get all active terms in this lexicon
    query = db.query(LexiconTerm).filter(
        LexiconTerm.lexicon_id == lexicon_id,
        LexiconTerm.is_active == True
    )
    
    if exclude_term_id:
        query = query.filter(LexiconTerm.id != exclude_term_id)
    
    all_terms = query.all()
    
    # Check for substring conflicts
    for existing_term in all_terms:
        existing_normalized = existing_term.normalized_term
        
        # Skip if it's the exact same term (handled by uniqueness check)
        if existing_normalized == normalized_term:
            continue
        
        # Check if new term contains existing term
        if existing_normalized in normalized_term:
            # The new term contains an existing term
            result.add_warning(
                "term",
                "contains_existing_term",
                term,
                existing_term=existing_term.term,
                existing_term_id=existing_term.id,
                message=f"Term '{term}' contains existing term '{existing_term.term}'"
            )
        
        # Check if existing term contains new term
        elif normalized_term in existing_normalized:
            # An existing term contains the new term
            result.add_warning(
                "term",
                "contained_in_existing_term",
                term,
                existing_term=existing_term.term,
                existing_term_id=existing_term.id,
                message=f"Term '{term}' is contained in existing term '{existing_term.term}'"
            )
    
    return result


def validate_term(
    db: Session,
    lexicon_id: str,
    term: str,
    replacement: str,
    exclude_term_id: Optional[int] = None,
    check_conflicts: bool = True
) -> ValidationResult:
    """
    Comprehensive validation of a lexicon term.
    
    Performs all validation checks:
    1. Format validation (length, empty strings)
    2. Uniqueness validation (case-insensitive)
    3. Circular replacement detection
    4. Conflict detection (optional, as it produces warnings)
    
    Args:
        db: Database session
        lexicon_id: The lexicon identifier
        term: The term to validate
        replacement: The replacement for the term
        exclude_term_id: Optional term ID to exclude (for updates)
        check_conflicts: Whether to check for overlapping terms (default: True)
    
    Returns:
        ValidationResult with all validation errors and warnings
    """
    combined_result = ValidationResult()
    
    # 1. Format validation
    format_result = validate_format(term, replacement)
    combined_result.errors.extend(format_result.errors)
    combined_result.warnings.extend(format_result.warnings)
    
    # If format validation fails, skip other checks
    if not format_result.is_valid:
        return combined_result
    
    # 2. Uniqueness validation
    uniqueness_result = validate_uniqueness(db, lexicon_id, term, exclude_term_id)
    combined_result.errors.extend(uniqueness_result.errors)
    combined_result.warnings.extend(uniqueness_result.warnings)
    
    # 3. Circular replacement detection
    circular_result = detect_circular_replacements(db, lexicon_id, term, replacement, exclude_term_id)
    combined_result.errors.extend(circular_result.errors)
    combined_result.warnings.extend(circular_result.warnings)
    
    # 4. Conflict detection (warnings only)
    if check_conflicts:
        conflict_result = detect_conflicts(db, lexicon_id, term, exclude_term_id)
        combined_result.warnings.extend(conflict_result.warnings)
    
    return combined_result


def validate_bulk_terms(
    db: Session,
    lexicon_id: str,
    terms: List[Tuple[str, str]],
    check_conflicts: bool = True
) -> Dict[int, ValidationResult]:
    """
    Validate multiple terms at once for bulk operations.
    
    This function checks:
    - Individual term validation
    - Uniqueness within the batch itself
    - Circular references within the batch
    
    Args:
        db: Database session
        lexicon_id: The lexicon identifier
        terms: List of (term, replacement) tuples
        check_conflicts: Whether to check for overlapping terms
    
    Returns:
        Dictionary mapping index -> ValidationResult for each term
    """
    results: Dict[int, ValidationResult] = {}
    
    # Track normalized terms in this batch
    batch_terms: Set[str] = set()
    batch_map: Dict[str, str] = {}  # normalized_term -> normalized_replacement
    
    for idx, (term, replacement) in enumerate(terms):
        result = ValidationResult()
        
        # Format validation
        format_result = validate_format(term, replacement)
        result.errors.extend(format_result.errors)
        result.warnings.extend(format_result.warnings)
        
        if format_result.is_valid:
            normalized_term = term.lower().strip()
            normalized_replacement = replacement.lower().strip()
            
            # Check for duplicates within the batch
            if normalized_term in batch_terms:
                result.add_error(
                    "term",
                    "duplicate_in_batch",
                    term,
                    message=f"Term '{term}' appears multiple times in this batch"
                )
            else:
                batch_terms.add(normalized_term)
                batch_map[normalized_term] = normalized_replacement
                
                # Check uniqueness against database
                uniqueness_result = validate_uniqueness(db, lexicon_id, term)
                result.errors.extend(uniqueness_result.errors)
                result.warnings.extend(uniqueness_result.warnings)
            
            # Check circular references (against DB + batch)
            circular_result = detect_circular_replacements(db, lexicon_id, term, replacement)
            result.errors.extend(circular_result.errors)
            result.warnings.extend(circular_result.warnings)
            
            # Check conflicts
            if check_conflicts:
                conflict_result = detect_conflicts(db, lexicon_id, term)
                result.warnings.extend(conflict_result.warnings)
        
        results[idx] = result
    
    return results
