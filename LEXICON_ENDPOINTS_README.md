# Lexicon Discovery Endpoints Implementation

## Overview

This document describes the implementation of lexicon discovery endpoints that allow clients to browse available lexicons and retrieve metadata about domain-specific terminology collections.

## Implemented Endpoints

### 1. GET /lexicons
**Purpose**: List all available lexicons with metadata

**Authentication**: Required (X-API-Key header)

**Response Format**:
```json
{
  "lexicons": [
    {
      "lexicon_id": "radiology",
      "term_count": 150,
      "last_updated": "2024-01-15T10:30:00Z",
      "description": "Medical radiology terminology"
    },
    {
      "lexicon_id": "cardiology",
      "term_count": 89,
      "last_updated": "2024-01-14T08:15:00Z",
      "description": "Cardiovascular and cardiac terminology"
    }
  ]
}
```

**Features**:
- Groups terms by `lexicon_id` from database
- Counts only active terms (`is_active=true`)
- Returns `MAX(updated_at)` as `last_updated`
- Results cached in Redis for 10 minutes

### 2. GET /lexicons/{lexicon_id}
**Purpose**: Get metadata for a specific lexicon

**Authentication**: Required (X-API-Key header)

**Response Format**:
```json
{
  "lexicon_id": "radiology",
  "term_count": 150,
  "last_updated": "2024-01-15T10:30:00Z",
  "description": "Medical radiology terminology"
}
```

**Response Codes**:
- `200`: Lexicon found and returned
- `404`: Lexicon not found or has no active terms
- `401`: Authentication failed

**Features**:
- Same aggregation as list endpoint, filtered by lexicon_id
- Returns 404 if lexicon doesn't exist or has 0 active terms
- Results cached in Redis for 10 minutes

## Implementation Details

### Files Created

1. **`app/models/lexicon.py`**
   - `LexiconTerm`: SQLAlchemy model for lexicon_terms table
   - `LexiconMetadata`: Pydantic response schema
   - `LexiconListResponse`: Schema for GET /lexicons
   - `LexiconDetailResponse`: Schema for GET /lexicons/{lexicon_id}

2. **`app/services/lexicon_service.py`**
   - `get_all_lexicons()`: Aggregates and returns all lexicons
   - `get_lexicon_by_id()`: Returns specific lexicon or None
   - `invalidate_lexicon_cache()`: Invalidates cache for specific lexicon
   - `invalidate_all_lexicon_caches()`: Invalidates all lexicon caches

3. **`app/routers/lexicons.py`**
   - Router with authentication dependency
   - GET /lexicons endpoint
   - GET /lexicons/{lexicon_id} endpoint
   - Comprehensive OpenAPI documentation

### Files Modified

1. **`app/main.py`**
   - Registered lexicons router

2. **`app/config/settings.py`**
   - Ensured REDIS_URL is available in get_settings()

3. **`app/models/__init__.py`**
   - Exported LexiconTerm model
   - Added Job model export
   - Added APIKey alias for backward compatibility

## Database Schema Requirements

The implementation expects a `lexicon_id` column in the `lexicon_terms` table:

```sql
ALTER TABLE lexicon_terms 
ADD COLUMN lexicon_id VARCHAR(100);

CREATE INDEX ix_lexicon_terms_lexicon_id ON lexicon_terms(lexicon_id);
```

**Note**: This should have been added by Task #16. If the column doesn't exist, the endpoints will fail at runtime with a database error.

## Caching Strategy

### Cache Keys
- All lexicons: `lexicons:all`
- Specific lexicon: `lexicons:detail:{lexicon_id}`

### TTL
- 10 minutes (600 seconds) for all cached data

### Cache Invalidation

Cache should be invalidated when lexicon terms are modified. CRUD endpoints should call:

```python
from app.services.lexicon_service import invalidate_lexicon_cache

# After creating/updating/deleting a term
invalidate_lexicon_cache(lexicon_id="radiology")  # Specific lexicon
# OR
invalidate_lexicon_cache()  # All lexicons
```

For bulk operations:
```python
from app.services.lexicon_service import invalidate_all_lexicon_caches

invalidate_all_lexicon_caches()
```

## Usage Examples

### List All Lexicons
```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/lexicons
```

### Get Specific Lexicon
```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/lexicons/radiology
```

### Python Client
```python
import requests

headers = {"X-API-Key": "your-api-key"}

# List all lexicons
response = requests.get("http://localhost:8000/lexicons", headers=headers)
lexicons = response.json()["lexicons"]

# Get specific lexicon
response = requests.get("http://localhost:8000/lexicons/radiology", headers=headers)
if response.status_code == 200:
    lexicon = response.json()
    print(f"Radiology has {lexicon['term_count']} terms")
elif response.status_code == 404:
    print("Lexicon not found")
```

## Testing Checklist

- [ ] GET /lexicons returns all lexicons with accurate counts
- [ ] Term counts only include active terms (is_active=true)
- [ ] last_updated reflects most recent modification
- [ ] GET /lexicons/{lexicon_id} returns correct metadata
- [ ] Returns 404 for lexicon_id with no terms
- [ ] Returns 404 for non-existent lexicon_id
- [ ] Metadata is cached in Redis
- [ ] Cache invalidates when terms are added/updated/deleted
- [ ] Endpoints require authentication (401 without X-API-Key)
- [ ] Responses match documented schema

## Dependencies

This implementation depends on:

1. **Task #16**: `lexicon_terms` table with `lexicon_id` column
2. **Task #23**: API key validation middleware (app/auth.py)
3. **Redis**: Running Redis instance at configured REDIS_URL
4. **PostgreSQL**: Database with lexicon_terms table

## Integration with CRUD Endpoints

When CRUD endpoints for lexicon terms are implemented (Task #26), they should:

1. Call `invalidate_lexicon_cache()` after any term modification
2. Pass the specific `lexicon_id` when known for efficiency
3. Use `invalidate_all_lexicon_caches()` for bulk operations

Example integration:
```python
from app.services.lexicon_service import invalidate_lexicon_cache

@router.post("/lexicons/{lexicon_id}/terms")
async def create_term(lexicon_id: str, term: TermCreate, db: Session = Depends(get_db)):
    # Create term in database
    new_term = LexiconTerm(**term.dict(), lexicon_id=lexicon_id)
    db.add(new_term)
    db.commit()
    
    # Invalidate cache
    invalidate_lexicon_cache(lexicon_id)
    
    return new_term
```

## Lexicon Descriptions

Lexicon descriptions are currently hardcoded in `app/services/lexicon_service.py`:

```python
LEXICON_DESCRIPTIONS = {
    "radiology": "Medical radiology terminology",
    "cardiology": "Cardiovascular and cardiac terminology",
    "general": "General medical terminology",
}
```

To add new lexicons, update this dictionary. In the future, this could be:
- Moved to a configuration file
- Stored in the database
- Made editable via API endpoints

## Performance Considerations

1. **Caching**: 10-minute TTL reduces database load for frequently accessed metadata
2. **Indexes**: Ensure `lexicon_id` and `is_active` columns are indexed
3. **Query Optimization**: Uses aggregation queries with GROUP BY for efficiency
4. **Redis Connection**: Reuses Redis client instance across requests

## Known Limitations

1. **lexicon_id Column**: Must exist in database (dependency on Task #16)
2. **Descriptions**: Currently hardcoded, not editable via API
3. **Cache Consistency**: Brief inconsistency window after term modifications
4. **No Pagination**: Returns all lexicons (acceptable for small numbers)

## Future Enhancements

- [ ] Store lexicon descriptions in database
- [ ] Add filtering/sorting options
- [ ] Add lexicon creation/deletion endpoints
- [ ] Add term preview in metadata response
- [ ] Add pagination for large numbers of lexicons
- [ ] Add WebSocket support for real-time updates
- [ ] Add metrics for cache hit rates
