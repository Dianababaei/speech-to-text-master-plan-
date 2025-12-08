# Lexicon Service Documentation

## Overview

The lexicon service provides core functionality for loading and caching domain-specific terminology mappings used in transcription post-processing. This enables swappable lexicons per request for different medical specialties or technical domains.

## Features

- **Flexible Selection**: Supports lexicon selection via HTTP header (`X-Lexicon-ID`) or query parameter (`?lexicon=`)
- **Redis Caching**: Caches loaded lexicons to minimize database queries
- **Graceful Degradation**: Falls back to database if Redis is unavailable
- **Cache Invalidation**: Provides function to invalidate cache when terms are modified

## Core Functions

### `load_lexicon(db: Session, lexicon_id: str) -> Dict[str, str]`

Async function to load lexicon terms with caching:
1. Checks Redis cache first (cache hit = fast response)
2. If not cached, loads from database
3. Stores in Redis cache with TTL for future requests
4. Returns dictionary of {term: replacement} pairs

### `load_lexicon_sync(db: Session, lexicon_id: str) -> Dict[str, str]`

Synchronous version for use in worker processes and non-async contexts.

### `invalidate_lexicon_cache(lexicon_id: str) -> bool`

Invalidates cached lexicon data. Should be called when terms are modified.

### `validate_lexicon_exists(db: Session, lexicon_id: str) -> bool`

Checks if a lexicon has any active terms in the database.

## Configuration

Environment variables (defined in `app/config/settings.py`):

- `DEFAULT_LEXICON`: Default lexicon to use if none specified (default: "general")
- `LEXICON_CACHE_TTL`: Cache time-to-live in seconds (default: 3600 = 1 hour)
- `REDIS_URL`: Redis connection URL (default: "redis://localhost:6379/0")

## Usage Examples

### In FastAPI Route (Async)

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_lexicon_id
from app.services.lexicon_service import load_lexicon

router = APIRouter()

@router.post("/process")
async def process_text(
    text: str,
    lexicon_id: str = Depends(get_lexicon_id),
    db: Session = Depends(get_db)
):
    # Load lexicon terms
    lexicon = await load_lexicon(db, lexicon_id)
    
    # Apply corrections
    # ... processing logic ...
    
    return {"processed": True}
```

### In Worker (Sync)

```python
from app.services.lexicon_service import load_lexicon_sync
from app.database import SessionLocal

def process_job(job_id: str, lexicon_id: str):
    db = SessionLocal()
    try:
        # Load lexicon terms synchronously
        lexicon = load_lexicon_sync(db, lexicon_id)
        
        # Apply corrections
        # ... processing logic ...
    finally:
        db.close()
```

### Extracting Lexicon ID (Dependency)

```python
from app.dependencies import get_lexicon_id

@router.post("/endpoint")
async def endpoint(
    lexicon_id: str = Depends(get_lexicon_id)
):
    # lexicon_id will be extracted from:
    # 1. X-Lexicon-ID header (priority)
    # 2. ?lexicon= query parameter
    # 3. DEFAULT_LEXICON config if neither provided
    pass
```

## Cache Invalidation Integration

### For CRUD Endpoints (Task #26)

When implementing CRUD endpoints for lexicon management, integrate cache invalidation as follows:

```python
from app.services.lexicon_service import invalidate_lexicon_cache

# After creating a term
@router.post("/lexicons/{lexicon_id}/terms")
async def create_term(lexicon_id: str, ...):
    # ... create term in database ...
    await invalidate_lexicon_cache(lexicon_id)
    return {"status": "created"}

# After updating a term
@router.put("/lexicons/{lexicon_id}/terms/{term_id}")
async def update_term(lexicon_id: str, term_id: str, ...):
    # ... update term in database ...
    await invalidate_lexicon_cache(lexicon_id)
    return {"status": "updated"}

# After deleting a term (soft delete)
@router.delete("/lexicons/{lexicon_id}/terms/{term_id}")
async def delete_term(lexicon_id: str, term_id: str, ...):
    # ... soft delete term (set is_active=False) ...
    await invalidate_lexicon_cache(lexicon_id)
    return {"status": "deleted"}
```

## Cache Behavior

### Cache Key Format
- Key: `lexicon:{lexicon_id}`
- Example: `lexicon:radiology`, `lexicon:cardiology`

### Cache Storage
- Value: JSON-serialized dictionary `{"term": "replacement", ...}`
- TTL: Configurable via `LEXICON_CACHE_TTL` (default: 1 hour)

### Cache Invalidation Triggers
- Term creation (POST)
- Term update (PUT)
- Term deletion (DELETE/soft delete)

### Cache Miss Behavior
1. Query database for active terms (`is_active=True`)
2. Build dictionary of {term: replacement}
3. Store in Redis with TTL
4. Return dictionary

## Error Handling

### Redis Unavailable
- Logs warning
- Falls back to database queries
- Application continues to function (degraded performance)

### Database Errors
- Logs error
- Raises exception to caller
- Should be handled at route level with appropriate HTTP status

### Empty Lexicon
- Returns empty dictionary `{}`
- No error raised
- Post-processing continues without lexicon corrections

## Logging

The service logs the following events:
- Cache hits/misses
- Database queries
- Cache invalidation
- Redis connection issues
- Errors and warnings

## Performance Considerations

- **First Request**: Database query + cache write (~10-50ms depending on lexicon size)
- **Cached Requests**: Redis lookup only (~1-5ms)
- **Cache Hit Ratio**: Typically >95% in production after warm-up
- **Memory Usage**: ~1-10KB per cached lexicon (depends on term count)

## Testing Cache Behavior

To test cache behavior in development:

```python
# Load lexicon (cache miss - queries database)
lexicon1 = await load_lexicon(db, "radiology")

# Load again (cache hit - uses Redis)
lexicon2 = await load_lexicon(db, "radiology")

# Invalidate cache
await invalidate_lexicon_cache("radiology")

# Load again (cache miss - queries database)
lexicon3 = await load_lexicon(db, "radiology")
```

## Future Enhancements

Potential improvements for future iterations:
- Pre-warming cache on application startup
- Metrics for cache hit ratio
- Bulk cache invalidation for all lexicons
- Cache versioning for zero-downtime updates
- Lexicon metadata caching (term count, last updated)
