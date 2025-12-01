# Database Connection Pooling and Session Management

This document describes the database connection pooling and session management implementation for the application.

## Overview

The database layer uses **SQLAlchemy** with connection pooling configured for efficient resource usage and proper lifecycle management in FastAPI applications.

## Architecture

### Components

1. **`app/config.py`** - Configuration management with environment variable support
2. **`app/database.py`** - SQLAlchemy engine, session factory, and dependency functions

### Connection Pool Configuration

The connection pool is configured with the following parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `pool_size` | 5 | Number of persistent connections maintained in the pool |
| `max_overflow` | 10 | Additional connections allowed beyond pool_size for burst capacity |
| `pool_pre_ping` | True | Test connections before use to prevent stale connection errors |
| `pool_recycle` | 3600 | Recycle connections after 1 hour (prevents long-lived connection issues) |
| `pool_timeout` | 30 | Maximum seconds to wait for an available connection |

## Configuration

### Environment Variables

Configure the database using environment variables:

```bash
# Database connection
DATABASE_URL=postgresql://user:password@host:port/database_name

# Pool configuration (optional, defaults shown)
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_RECYCLE=3600
DB_POOL_PRE_PING=true

# Development settings
DB_ECHO=false              # Set to true to log all SQL queries
ENVIRONMENT=dev            # dev, test, or production
```

### Example `.env` file

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/transcription_db
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_ECHO=false
ENVIRONMENT=dev
```

## Usage

### In FastAPI Endpoints

Use the `get_db()` dependency function to inject a database session into your endpoints:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter()

@router.get("/items")
def get_items(db: Session = Depends(get_db)):
    """Get all items from the database."""
    items = db.query(Item).all()
    return items

@router.post("/items")
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    """Create a new item."""
    db_item = Item(**item.dict())
    db.add(db_item)
    db.flush()  # Commit happens automatically via dependency
    return db_item
```

### Session Lifecycle

The `get_db()` dependency automatically manages the session lifecycle:

1. **Create** - A new session is created at the start of each request
2. **Use** - The session is yielded to your endpoint function
3. **Commit** - If no exceptions occur, changes are committed
4. **Rollback** - If an exception occurs, changes are rolled back
5. **Close** - The session is always closed (returns connection to pool)

### Outside of FastAPI Context

For background tasks, CLI scripts, or other non-request contexts, use the `get_db_session()` context manager:

```python
from app.database import get_db_session

def background_task():
    """Example background task using database."""
    with get_db_session() as db:
        items = db.query(Item).filter(Item.status == "pending").all()
        for item in items:
            item.status = "processed"
        # Commit happens automatically when exiting context
```

## Error Handling

The database module includes comprehensive error handling:

### Connection Errors

Connection errors are logged with appropriate severity:

```python
# Automatic retry for transient failures
if not test_database_connection(max_retries=3, retry_delay=2):
    logger.error("Database unavailable after retries")
```

### Transaction Errors

SQLAlchemy errors trigger automatic rollback:

```python
try:
    # Your database operations
    db.add(item)
    db.flush()
except exc.SQLAlchemyError as e:
    # Automatic rollback via get_db() dependency
    logger.error(f"Database error: {e}")
```

## Testing Database Connection

Test the database connection before starting the application:

```python
from app.database import test_database_connection

if __name__ == "__main__":
    if test_database_connection():
        print("✓ Database connection successful")
    else:
        print("✗ Database connection failed")
```

## Monitoring

Check pool status for monitoring and debugging:

```python
from app.database import get_db_pool_status

status = get_db_pool_status()
print(f"Pool size: {status['size']}")
print(f"Checked out: {status['checked_out']}")
print(f"Overflow: {status['overflow']}")
```

## Best Practices

### DO

✓ Use `Depends(get_db)` for all FastAPI endpoints  
✓ Let the dependency handle commit/rollback/close  
✓ Use `db.flush()` when you need the ID before commit  
✓ Set `DB_ECHO=true` in development for debugging  
✓ Monitor pool status in production  

### DON'T

✗ Don't manually commit in endpoints (dependency handles it)  
✗ Don't forget to close sessions in non-FastAPI contexts  
✗ Don't set `DB_ECHO=true` in production (performance impact)  
✗ Don't use global session objects  
✗ Don't bypass the connection pool  

## Scaling Considerations

### Small Scale (1-10 concurrent users)
- `pool_size=5`, `max_overflow=10` (default)
- Single application instance

### Medium Scale (10-50 concurrent users)
- `pool_size=10`, `max_overflow=20`
- Multiple application instances
- Consider connection limits on PostgreSQL server

### Large Scale (50+ concurrent users)
- `pool_size=20`, `max_overflow=30`
- Multiple application instances with load balancing
- PgBouncer or similar connection pooler recommended
- Monitor and tune based on actual usage patterns

### PostgreSQL Connection Limit

PostgreSQL has a maximum connection limit (default: 100). Calculate total connections:

```
Total = (pool_size + max_overflow) × number_of_app_instances
```

Ensure this doesn't exceed PostgreSQL's `max_connections` setting.

## Troubleshooting

### Connection Pool Exhausted

**Symptom**: Application hangs or times out waiting for connections

**Solutions**:
1. Increase `DB_POOL_SIZE` or `DB_MAX_OVERFLOW`
2. Check for connection leaks (sessions not closed)
3. Review slow queries blocking connections
4. Scale horizontally with more app instances

### Stale Connections

**Symptom**: Random database errors about closed connections

**Solutions**:
1. Ensure `DB_POOL_PRE_PING=true` (default)
2. Reduce `DB_POOL_RECYCLE` time
3. Check PostgreSQL timeout settings

### Connection Errors on Startup

**Symptom**: Application fails to start with connection errors

**Solutions**:
1. Verify `DATABASE_URL` is correct
2. Ensure PostgreSQL is running and accessible
3. Check network/firewall settings
4. Use `test_database_connection()` with retries

## Example Application Integration

```python
# main.py
from fastapi import FastAPI
from app.database import test_database_connection
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="Speech-to-Text API")

@app.on_event("startup")
async def startup_event():
    """Test database connection on startup."""
    logger.info("Testing database connection...")
    if test_database_connection(max_retries=5, retry_delay=2):
        logger.info("✓ Database connected successfully")
    else:
        logger.error("✗ Failed to connect to database")
        raise RuntimeError("Database connection failed")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Application shutting down...")

# Include your routers
# app.include_router(transcription_router)
```

## Additional Resources

- [SQLAlchemy Connection Pooling Docs](https://docs.sqlalchemy.org/en/14/core/pooling.html)
- [FastAPI Database Dependencies](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [PostgreSQL Connection Management](https://www.postgresql.org/docs/current/runtime-config-connection.html)
