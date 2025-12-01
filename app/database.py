"""
Database connection and session management module.

This module provides:
- SQLAlchemy engine with connection pooling
- Session factory for database operations
- FastAPI dependency injection function for database sessions

Connection Pool Configuration:
    - pool_size: 5 persistent connections (configurable via env)
    - max_overflow: 10 additional connections for burst capacity
    - pool_pre_ping: Test connections before use (prevents stale connections)
    - pool_recycle: Recycle connections after 1 hour (3600 seconds)

Session Lifecycle:
    - Created on request (via FastAPI dependency injection)
    - Automatically committed on success
    - Rolled back on exceptions
    - Always closed in finally block (prevents connection leaks)

Usage in FastAPI:
    @app.get("/items")
    def get_items(db: Session = Depends(get_db)):
        return db.query(Item).all()
"""

import logging
import time
from typing import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event, exc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import Pool

from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# SQLAlchemy Engine Configuration
# ================================
# The engine manages the connection pool and provides the interface to the database

try:
    engine = create_engine(
        settings.database_url,
        # Connection pool configuration
        pool_size=settings.db_pool_size,          # Number of persistent connections
        max_overflow=settings.db_max_overflow,    # Additional connections for bursts
        pool_recycle=settings.db_pool_recycle,    # Recycle connections after 1 hour
        pool_pre_ping=settings.db_pool_pre_ping,  # Test connections before using
        
        # Development/debugging settings
        echo=settings.db_echo,                     # Log all SQL statements (dev only)
        
        # Connection behavior
        pool_timeout=30,                           # Timeout waiting for connection (seconds)
        connect_args={
            "connect_timeout": 10,                 # PostgreSQL connection timeout
        }
    )
    logger.info("Database engine created successfully")
    logger.info(f"Connection pool configured: size={settings.db_pool_size}, "
                f"max_overflow={settings.db_max_overflow}, "
                f"recycle={settings.db_pool_recycle}s")
    
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise


# Connection Pool Event Listeners
# ================================
# These listeners help with debugging and monitoring connection pool behavior

@event.listens_for(Pool, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log when a new database connection is established."""
    logger.debug(f"New database connection established: {id(dbapi_conn)}")


@event.listens_for(Pool, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log when a connection is checked out from the pool."""
    logger.debug(f"Connection checked out from pool: {id(dbapi_conn)}")


@event.listens_for(Pool, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """Log when a connection is returned to the pool."""
    logger.debug(f"Connection returned to pool: {id(dbapi_conn)}")


# Session Factory
# ===============
# SessionLocal is a factory for creating new database sessions

SessionLocal = sessionmaker(
    autocommit=False,      # Manual transaction control
    autoflush=False,       # Manual flush control for better performance
    bind=engine,           # Bind to our configured engine
    expire_on_commit=True  # Expire all instances after commit (prevents stale data)
)

logger.info("Session factory configured successfully")


# FastAPI Dependency Function
# ============================
# This function is used with FastAPI's dependency injection system

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.
    
    This function:
    1. Creates a new session for each request
    2. Yields the session to the endpoint
    3. Commits the transaction if no exceptions occur
    4. Rolls back on exceptions
    5. Always closes the session in the finally block
    
    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    
    Yields:
        Session: SQLAlchemy database session
        
    Raises:
        DatabaseError: On connection or query failures (after logging)
    """
    db = SessionLocal()
    try:
        logger.debug("Database session created")
        yield db
        # If we reach here without exception, commit the transaction
        db.commit()
        logger.debug("Database session committed")
    except exc.SQLAlchemyError as e:
        # Roll back on any database errors
        db.rollback()
        logger.error(f"Database error occurred, rolling back: {e}")
        raise
    except Exception as e:
        # Roll back on any other errors
        db.rollback()
        logger.error(f"Unexpected error occurred, rolling back: {e}")
        raise
    finally:
        # Always close the session to return connection to pool
        db.close()
        logger.debug("Database session closed")


# Connection Testing and Retry Logic
# ===================================

def test_database_connection(max_retries: int = 3, retry_delay: int = 2) -> bool:
    """
    Test database connection with retry logic for transient failures.
    
    This function attempts to connect to the database and execute a simple
    query. It retries on connection failures to handle transient issues
    (e.g., database container starting up).
    
    Args:
        max_retries: Maximum number of connection attempts (default: 3)
        retry_delay: Seconds to wait between retries (default: 2)
    
    Returns:
        bool: True if connection successful, False otherwise
    
    Example:
        if test_database_connection():
            logger.info("Database is ready")
        else:
            logger.error("Database is unavailable")
    """
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Testing database connection (attempt {attempt}/{max_retries})")
            
            # Try to connect and execute a simple query
            with engine.connect() as connection:
                connection.execute("SELECT 1")
            
            logger.info("Database connection test successful")
            return True
            
        except exc.OperationalError as e:
            logger.warning(f"Database connection attempt {attempt} failed: {e}")
            
            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error(f"Failed to connect to database after {max_retries} attempts")
                return False
                
        except Exception as e:
            logger.error(f"Unexpected error during connection test: {e}")
            return False
    
    return False


def get_db_pool_status() -> dict:
    """
    Get current connection pool status for monitoring.
    
    Returns:
        dict: Pool statistics including size, checked out connections, etc.
        
    Example:
        status = get_db_pool_status()
        print(f"Pool size: {status['size']}, Checked out: {status['checked_out']}")
    """
    pool = engine.pool
    
    return {
        "size": pool.size(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "pool_size_config": settings.db_pool_size,
        "max_overflow_config": settings.db_max_overflow,
    }


# Context Manager for Manual Session Management
# ==============================================
# For use outside of FastAPI request context (e.g., scripts, background tasks)

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for manual database session management.
    
    Use this when you need a database session outside of FastAPI's
    request/response cycle (e.g., in background tasks, CLI scripts).
    
    Usage:
        with get_db_session() as db:
            items = db.query(Item).all()
            # Session is automatically committed and closed
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error in database session: {e}")
        raise
    finally:
        db.close()
