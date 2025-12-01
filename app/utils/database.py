"""
Database session management utilities.
"""
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import DATABASE_URL

# Create engine
engine = create_engine(DATABASE_URL, echo=False)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session() -> Session:
    """
    Get a new database session.
    
    Returns:
        Session: SQLAlchemy database session
    """
    return SessionLocal()


@contextmanager
def db_session_context():
    """
    Context manager for database sessions with automatic commit/rollback.
    
    Usage:
        with db_session_context() as session:
            # do database operations
            pass
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
