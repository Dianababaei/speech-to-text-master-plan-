"""
Database session management utilities.
"""
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config.settings import get_settings

settings = get_settings()

# Create engine
engine = create_engine(settings.DATABASE_URL, echo=False)

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
