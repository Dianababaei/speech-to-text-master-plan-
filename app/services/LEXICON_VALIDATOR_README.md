# Lexicon Validation Service

## Overview

The `lexicon_validator.py` module provides comprehensive validation and conflict detection logic for lexicon terms to ensure data integrity and prevent operational issues during transcription post-processing.

## Validation Rules

### 1. Term Uniqueness
- **Rule**: No duplicate terms within the same `lexicon_id` (case-insensitive)
- **Implementation**: Uses `normalized_term` column for efficient lookups
- **Error Type**: `duplicate`
- **Example**: Cannot add "MRI" if "mri" already exists

### 2. Format Validation
- **Term Length**: 1-200 characters
- **Replacement Length**: 1-500 characters
- **No Empty Strings**: Terms and replacements cannot be empty or whitespace-only
- **Whitespace Handling**: Leading/trailing whitespace triggers warnings and is auto-trimmed
- **Error Types**: `empty_or_whitespace`, `too_short`, `too_long`

### 3. Circular Replacement Detection
- **Rule**: Identify chains where term A → term B → term A (or longer cycles)
- **Implementation**: Graph traversal using depth-first search (DFS)
- **Error Type**: `circular_reference`
- **Examples**:
  - Direct cycle: "MRI" → "magnetic resonance" and "magnetic resonance" → "MRI"
  - Longer cycle: "A" → "B" → "C" → "A"
  - Self-reference: "test" → "test"

### 4. Conflict Detection
- **Rule**: Identify overlapping patterns where multiple terms could match the same text
- **Warning Types**: 
  - `contains_existing_term`: New term contains an existing term (e.g., adding "MRI scan" when "MRI" exists)
  - `contained_in_existing_term`: New term is contained in an existing term (e.g., adding "MRI" when "MRI scan" exists)
- **Note**: These are warnings, not errors, as they may be intentional

## API Reference

### Core Functions

#### `validate_term()`
Comprehensive validation of a single lexicon term.

```python
from app.services.lexicon_validator import validate_term

validation_result = validate_term(
    db=db,
    lexicon_id="radiology",
    term="atreal fibrillation",
    replacement="atrial fibrillation",
    exclude_term_id=None,  # Optional: for updates
    check_conflicts=True
)

if not validation_result.is_valid:
    # Handle errors
    errors = validation_result.to_error_detail()
```

**Parameters:**
- `db`: SQLAlchemy database session
- `lexicon_id`: Lexicon identifier (e.g., "radiology")
- `term`: The term to validate
- `replacement`: The replacement for the term
- `exclude_term_id`: Optional term ID to exclude from checks (for updates)
- `check_conflicts`: Whether to check for overlapping terms (default: True)

**Returns:** `ValidationResult` object

#### `validate_bulk_terms()`
Validate multiple terms at once for bulk import operations.

```python
from app.services.lexicon_validator import validate_bulk_terms

terms = [
    ("CT scan", "CT scan"),
    ("MRI", "MRI"),
    ("atreal fibrillation", "atrial fibrillation")
]

results = validate_bulk_terms(
    db=db,
    lexicon_id="radiology",
    terms=terms,
    check_conflicts=True
)

# Check each result
for idx, result in results.items():
    if not result.is_valid:
        print(f"Term {idx} failed validation: {result.errors}")
```

**Parameters:**
- `db`: SQLAlchemy database session
- `lexicon_id`: Lexicon identifier
- `terms`: List of `(term, replacement)` tuples
- `check_conflicts`: Whether to check for overlapping terms

**Returns:** Dictionary mapping index → `ValidationResult`

#### Individual Validation Functions

```python
# Format validation only
format_result = validate_format(term, replacement)

# Uniqueness check only
uniqueness_result = validate_uniqueness(db, lexicon_id, term, exclude_term_id)

# Circular reference detection only
circular_result = detect_circular_replacements(db, lexicon_id, term, replacement, exclude_term_id)

# Conflict detection only
conflict_result = detect_conflicts(db, lexicon_id, term, exclude_term_id)
```

### ValidationResult Class

```python
class ValidationResult:
    errors: List[ValidationError]      # Critical errors that prevent creation/update
    warnings: List[ValidationError]    # Non-critical issues (informational)
    
    @property
    def is_valid(self) -> bool:
        """Returns True if no errors (warnings are OK)"""
    
    @property
    def has_warnings(self) -> bool:
        """Returns True if there are warnings"""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
    
    def to_error_detail(self, message: str) -> Dict:
        """Convert to FastAPI HTTPException detail format"""
```

## Error Response Format

When validation fails, the API returns a structured error response:

```json
{
  "detail": {
    "error_type": "validation_error",
    "message": "Term validation failed",
    "errors": [
      {
        "field": "term",
        "issue": "duplicate",
        "value": "MRI",
        "existing_term_id": 42,
        "existing_term": "mri",
        "message": "Term 'MRI' already exists in lexicon 'radiology'"
      },
      {
        "field": "replacement",
        "issue": "circular_reference",
        "value": "magnetic resonance",
        "chain": ["MRI", "magnetic resonance", "MRI"],
        "message": "Circular replacement detected: MRI → magnetic resonance → MRI"
      }
    ]
  }
}
```

## Integration with Endpoints

### POST `/lexicons/{lexicon_id}/terms`

```python
from app.services.lexicon_validator import validate_term

@router.post("/{lexicon_id}/terms")
async def create_term(lexicon_id: str, term_data: TermCreate, db: Session = Depends(get_db)):
    # Validate
    validation_result = validate_term(db, lexicon_id, term_data.term, term_data.replacement)
    
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=422,
            detail=validation_result.to_error_detail("Term validation failed")
        )
    
    # Create term...
```

### PUT `/lexicons/{lexicon_id}/terms/{term_id}`

```python
@router.put("/{lexicon_id}/terms/{term_id}")
async def update_term(
    lexicon_id: str, 
    term_id: int, 
    term_data: TermUpdate, 
    db: Session = Depends(get_db)
):
    # Validate (exclude current term from uniqueness check)
    validation_result = validate_term(
        db, 
        lexicon_id, 
        term_data.term, 
        term_data.replacement,
        exclude_term_id=term_id
    )
    
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=422,
            detail=validation_result.to_error_detail("Term validation failed")
        )
    
    # Update term...
```

### Bulk Import (Future Implementation)

```python
@router.post("/{lexicon_id}/terms/bulk")
async def bulk_import_terms(
    lexicon_id: str,
    terms: List[TermCreate],
    db: Session = Depends(get_db)
):
    # Convert to tuple format
    term_tuples = [(t.term, t.replacement) for t in terms]
    
    # Validate all at once
    results = validate_bulk_terms(db, lexicon_id, term_tuples)
    
    # Check for any errors
    failed_indices = [idx for idx, result in results.items() if not result.is_valid]
    
    if failed_indices:
        # Return detailed errors for each failed term
        errors = {idx: results[idx].to_dict() for idx in failed_indices}
        raise HTTPException(
            status_code=422,
            detail={
                "error_type": "bulk_validation_error",
                "message": f"Validation failed for {len(failed_indices)} term(s)",
                "failed_terms": errors
            }
        )
    
    # Import terms...
```

## Edge Cases and Special Handling

### Unicode Characters
- **Supported**: Full Unicode support (UTF-8)
- **Example**: "Crohn's disease", "β-blocker", "naïve"
- **Handling**: Python 3 native string support, PostgreSQL VARCHAR with UTF-8

### Special Characters
- **Allowed**: Hyphens, apostrophes, spaces, parentheses, etc.
- **Medical examples**: "T-cell", "Crohn's disease", "5-HT receptor"
- **Reasoning**: Medical terminology requires special characters

### Whitespace
- **Leading/trailing**: Automatically trimmed with warnings
- **Internal**: Preserved (e.g., "CT scan" remains "CT scan")
- **Multiple spaces**: Preserved (may want to normalize in future)

### Case Sensitivity
- **Storage**: Original case preserved in `term` column
- **Matching**: Case-insensitive via `normalized_term` column
- **Example**: "MRI", "mri", "Mri" are all treated as the same term

### Very Long Terms
- **Term limit**: 200 characters (reasonable for medical terminology)
- **Replacement limit**: 500 characters (allows for longer descriptions)
- **Rationale**: Balance between flexibility and preventing abuse

### Empty Lexicons
- **First term**: No conflicts possible, only format validation
- **Circular detection**: Cannot create cycles with no existing terms

## Performance Considerations

### Single Term Validation
- **Format validation**: O(1) - instant
- **Uniqueness check**: O(1) - indexed database lookup
- **Circular detection**: O(n) - where n = number of terms in lexicon
- **Conflict detection**: O(n) - linear scan of existing terms

### Bulk Validation
- **Batch uniqueness**: Single query for all existing terms
- **Within-batch duplicates**: O(n) with set lookups
- **Circular detection**: Builds graph once, checks each term
- **Recommended batch size**: Up to 1000 terms per request

### Optimization Tips
1. **Use bulk validation** for imports (single DB query vs. multiple)
2. **Skip conflict detection** if not needed (`check_conflicts=False`)
3. **Index normalized_term** column (should exist from schema)
4. **Cache results** for repeated validations of same data

## Testing

### Manual Testing

```python
from app.database import SessionLocal
from app.services.lexicon_validator import validate_term

db = SessionLocal()

# Test 1: Valid term
result = validate_term(db, "radiology", "CT scan", "computed tomography scan")
assert result.is_valid

# Test 2: Duplicate term (case-insensitive)
# Assuming "ct scan" already exists
result = validate_term(db, "radiology", "CT SCAN", "computed tomography")
assert not result.is_valid
assert result.errors[0].issue == "duplicate"

# Test 3: Circular reference
# Setup: Add "MRI" → "magnetic resonance"
# Then try: Add "magnetic resonance" → "MRI"
result = validate_term(db, "radiology", "magnetic resonance", "MRI")
assert not result.is_valid
assert result.errors[0].issue == "circular_reference"

# Test 4: Format validation
result = validate_term(db, "radiology", "  ", "test")
assert not result.is_valid
assert result.errors[0].issue == "empty_or_whitespace"

# Test 5: Overlapping terms (warning)
# Setup: Add "MRI"
# Then: Add "MRI scan"
result = validate_term(db, "radiology", "MRI scan", "magnetic resonance imaging scan")
assert result.is_valid  # Just a warning
assert result.has_warnings
assert result.warnings[0].issue == "contains_existing_term"

db.close()
```

### Unit Test Examples

See `tests/test_lexicon_validator.py` for comprehensive unit tests.

## Success Criteria Checklist

- [x] Cannot create duplicate terms within same lexicon (case-insensitive)
- [x] Cannot create circular replacements (A→B→A or longer chains)
- [x] Invalid formats (empty strings, excessive length) are rejected with clear messages
- [x] Overlapping terms are detected and reported as warnings
- [x] All validation errors include specific details about what failed and why
- [x] Validation runs efficiently even for bulk operations (batch queries)
- [x] Handles Unicode characters correctly
- [x] Handles special characters in medical terms
- [x] Handles very long terms with clear length limit errors
- [x] Returns structured error responses with specific validation failure details
- [x] Integrated into POST and PUT endpoints for lexicon terms

## Future Enhancements

1. **Phonetic Similarity**: Detect terms that sound similar (e.g., "their" vs "there")
2. **Synonym Detection**: Warn about terms with similar meanings
3. **Multi-word Overlap**: Detect when adding "MRI" would affect "MRI scan" replacement
4. **Custom Rules**: Allow lexicon-specific validation rules
5. **Batch Optimization**: Parallel validation for very large imports
6. **Caching**: Cache validation results for repeated checks
7. **Fuzzy Matching**: Detect near-duplicates (e.g., "CT-scan" vs "CT scan")
