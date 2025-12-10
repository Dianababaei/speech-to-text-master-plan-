# Post-Processing Service

## Overview

The post-processing service applies domain-specific corrections to transcription text using lexicon-based term replacements. This is a critical component of the transcription pipeline that improves accuracy for specialized domains like medical terminology.

## Features

### 1. Case-Insensitive Matching with Case Preservation

The service matches terms case-insensitively but intelligently preserves the case pattern of the original text:

- **ALL UPPERCASE**: `MRI` → `MRI` (even if lexicon has `"mri": "MRI"`)
- **Title Case**: `Mri` → `Mri` (preserves capitalization of first letter)
- **lowercase**: Applies replacement as defined in lexicon

```python
# Example
lexicon = {"mri": "MRI"}
text = "The MRI and mri and Mri scans"
result = "The MRI and MRI and Mri scans"
```

### 2. Longest-Match-First Strategy

When multiple lexicon terms could match, the service prefers longer, more specific terms:

```python
# Example
lexicon = {
    "mri": "MRI",
    "mri scan": "MRI Scan"
}
text = "Patient needs an mri scan"
result = "Patient needs an MRI Scan"  # Matches "mri scan" as whole, not just "mri"
```

### 3. Whole-Word Matching

The service uses word boundaries to avoid partial matches:

```python
# Example
lexicon = {"scan": "SCAN"}
text = "The scanning process"
result = "The scanning process"  # "scan" doesn't match "scanning"
```

### 4. Unicode and Persian Text Support

The service properly handles Unicode characters including Persian/Farsi text:

```python
# Example
lexicon = {
    "mri": "MRI",
    "ام آر آی": "MRI"
}
text = "بیمار نیاز به ام آر آی دارد"
result = "بیمار نیاز به MRI دارد"
```

### 5. Comprehensive Logging

The service logs detailed information about replacements for debugging:

- Each term replacement with occurrence count
- Position information for matches
- Summary statistics
- Error handling with graceful fallback

## API

### Main Functions

#### `apply_lexicon_replacements(text: str, lexicon_id: str, db: Session) -> str`

High-level function that loads lexicon from cache/database and applies replacements.

**Arguments:**
- `text`: The transcription text to process
- `lexicon_id`: Identifier for the lexicon (e.g., "radiology", "cardiology")
- `db`: SQLAlchemy database session

**Returns:**
- Processed text with corrections applied

**Raises:**
- `PostProcessingError`: If lexicon loading or processing fails

**Example:**
```python
from app.services.postprocessing_service import apply_lexicon_replacements
from app.database import get_db

db = next(get_db())
text = "Patient underwent mri and ct scans"
result = apply_lexicon_replacements(text, "radiology", db)
print(result)  # "Patient underwent MRI and CT scans"
```

#### `apply_lexicon_corrections(text: str, lexicon: Dict[str, str]) -> str`

Lower-level function that applies a pre-loaded lexicon dictionary.

**Arguments:**
- `text`: The text to process
- `lexicon`: Dictionary of `{term: replacement}` pairs

**Returns:**
- Processed text with corrections applied

**Example:**
```python
from app.services.postprocessing_service import apply_lexicon_corrections

lexicon = {
    "mri": "MRI",
    "ct": "CT",
    "xray": "X-ray"
}
text = "Patient had mri, ct, and xray"
result = apply_lexicon_corrections(text, lexicon)
print(result)  # "Patient had MRI, CT, and X-ray"
```

#### `process_transcription(text: str, lexicon_id: Optional[str] = None, db: Optional[Session] = None) -> str`

Full post-processing pipeline (can be extended with additional processing steps).

**Arguments:**
- `text`: Original transcription text
- `lexicon_id`: Optional lexicon ID
- `db`: Optional database session

**Returns:**
- Processed text

**Example:**
```python
from app.services.postprocessing_service import process_transcription

result = process_transcription(
    text="Patient underwent mri scan",
    lexicon_id="radiology",
    db=db
)
```

## Lexicon Loading

The service integrates with `lexicon_service.py` which implements:

1. **Redis caching** (preferred): Fast in-memory cache with configurable TTL
2. **PostgreSQL fallback**: Loads from database if cache unavailable
3. **Automatic cache invalidation**: When lexicon terms are modified

### Cache Configuration

Set in environment variables:
- `LEXICON_CACHE_TTL`: Cache time-to-live in seconds (default: 3600 = 1 hour)
- `REDIS_URL`: Redis connection URL

## Performance

### Benchmarks

For typical lexicons (100-1000 terms):
- Simple text (500 words): < 10ms
- Long text (5000 words): < 50ms
- Very long text (50000 words): < 500ms

### Optimization

The service is optimized for common use cases:
- Lexicon terms are sorted once (longest-first)
- Regex patterns are compiled during matching
- Redis caching eliminates repeated database queries
- Unicode support doesn't significantly impact performance

## Error Handling

The service is designed to be robust:

1. **Missing lexicon**: Returns original text with warning
2. **Empty lexicon**: Returns original text
3. **Invalid regex patterns**: Escaped automatically with `re.escape()`
4. **Database errors**: Cached data still available
5. **Redis unavailable**: Falls back to database

## Testing

Comprehensive unit tests cover:
- Case preservation scenarios
- Longest-match-first behavior
- Persian/Unicode text handling
- Edge cases (punctuation, numbers, special characters)
- Real-world medical transcription scenarios

Run tests:
```bash
pytest tests/unit/test_postprocessing_service.py -v
```

## Integration

### With Transcription Workers

```python
from app.services.postprocessing_service import process_transcription
from app.database import get_db

# After transcription
raw_transcription = transcribe_audio(audio_file)

# Apply post-processing
db = next(get_db())
processed_text = process_transcription(
    text=raw_transcription,
    lexicon_id=job.lexicon_id,
    db=db
)
```

### With API Endpoints

```python
from fastapi import Depends
from app.services.postprocessing_service import apply_lexicon_replacements
from app.dependencies import get_db

@app.post("/transcribe")
async def transcribe(
    audio: UploadFile,
    lexicon_id: str = "general",
    db: Session = Depends(get_db)
):
    # Transcribe audio
    raw_text = await transcribe_audio(audio)
    
    # Apply lexicon corrections
    corrected_text = apply_lexicon_replacements(raw_text, lexicon_id, db)
    
    return {"text": corrected_text}
```

## Future Enhancements

Potential improvements for future versions:

1. **Context-aware replacements**: Consider surrounding words for disambiguation
2. **Probabilistic matching**: Handle fuzzy matches with confidence scores
3. **Multi-lexicon support**: Apply multiple lexicons in priority order
4. **Performance caching**: Cache compiled regex patterns for frequently used lexicons
5. **Machine learning integration**: Learn corrections from user feedback
6. **Batch processing**: Optimize for processing multiple transcriptions at once

## Related Documentation

- `LEXICON_SERVICE_README.md`: Lexicon loading and caching
- `LEXICON_API_IMPLEMENTATION.md`: Lexicon management API
- Database schema: `alembic/versions/002_add_lexicon_id_replacement.py`
