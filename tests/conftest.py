"""
Shared pytest fixtures for all tests.

This module provides reusable fixtures for:
- Database sessions with transaction rollback
- Redis client connections
- FastAPI test client
- Mock services (OpenAI, authentication)
- Test data factories
"""

import os
import pytest
import asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, MagicMock, patch

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
import redis

from app.models import Base
from app.database import get_db
from app.config.settings import get_settings, Settings
from app.main import app


# ============================================================================
# Environment Setup
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables before any tests run."""
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["REDIS_URL"] = "redis://localhost:6379/15"  # Use DB 15 for tests
    os.environ["OPENAI_API_KEY"] = "test-api-key-12345"
    yield
    # Cleanup after all tests
    os.environ.pop("TESTING", None)


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_engine():
    """
    Create a test database engine.
    
    Uses SQLite in-memory database for fast, isolated tests.
    Scope is session to create tables only once.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Drop all tables after tests
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """
    Create a database session for a test with automatic rollback.
    
    Each test gets a fresh session that's rolled back after the test,
    ensuring test isolation.
    
    Yields:
        Session: SQLAlchemy database session
    """
    # Create a connection
    connection = test_engine.connect()
    
    # Begin a transaction
    transaction = connection.begin()
    
    # Create a session bound to the connection
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestSessionLocal()
    
    # Enable nested transactions for savepoints
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            session.begin_nested()
    
    session.begin_nested()
    
    yield session
    
    # Rollback the transaction
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def override_get_db(db_session):
    """
    Override the FastAPI dependency to use test database session.
    
    This fixture should be used with the test_client fixture to ensure
    API endpoints use the test database.
    """
    def _get_test_db():
        try:
            yield db_session
        finally:
            pass  # Session cleanup handled by db_session fixture
    
    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


# ============================================================================
# Redis Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def redis_available():
    """Check if Redis is available for testing."""
    try:
        client = redis.from_url("redis://localhost:6379/15", socket_connect_timeout=1)
        client.ping()
        client.close()
        return True
    except (redis.ConnectionError, redis.TimeoutError):
        return False


@pytest.fixture(scope="function")
def redis_client(redis_available):
    """
    Provide a Redis client for tests.
    
    Uses database 15 to avoid conflicts with development data.
    Flushes the database before and after each test.
    
    Yields:
        redis.Redis: Redis client instance
    """
    if not redis_available:
        pytest.skip("Redis is not available")
    
    client = redis.from_url(
        "redis://localhost:6379/15",
        decode_responses=True,
        socket_connect_timeout=5
    )
    
    # Flush test database before test
    client.flushdb()
    
    yield client
    
    # Flush test database after test
    client.flushdb()
    client.close()


@pytest.fixture(scope="function")
def mock_redis_client():
    """
    Provide a mock Redis client for tests that don't need real Redis.
    
    Returns:
        MagicMock: Mock Redis client
    """
    mock_client = MagicMock(spec=redis.Redis)
    mock_client.ping.return_value = True
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    mock_client.delete.return_value = 1
    mock_client.exists.return_value = False
    return mock_client


# ============================================================================
# FastAPI Test Client Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_client(override_get_db) -> Generator[TestClient, None, None]:
    """
    Provide a FastAPI test client with database override.
    
    Use this fixture to test API endpoints with a test database.
    
    Yields:
        TestClient: FastAPI test client
    """
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
def api_client(test_client) -> TestClient:
    """
    Alias for test_client with a more descriptive name.
    
    Returns:
        TestClient: FastAPI test client
    """
    return test_client


# ============================================================================
# Authentication Fixtures
# ============================================================================

@pytest.fixture
def auth_headers():
    """
    Provide authentication headers for API tests.
    
    Returns:
        dict: Headers dictionary with authentication token
    """
    return {
        "Authorization": "Bearer test-token-12345",
        "Content-Type": "application/json"
    }


@pytest.fixture
def admin_auth_headers():
    """
    Provide admin authentication headers for API tests.
    
    Returns:
        dict: Headers dictionary with admin authentication token
    """
    return {
        "Authorization": "Bearer admin-token-12345",
        "Content-Type": "application/json",
        "X-Admin-Role": "true"
    }


# ============================================================================
# Mock Service Fixtures
# ============================================================================

@pytest.fixture
def mock_openai_client():
    """
    Provide a mock OpenAI client for tests.
    
    Returns:
        MagicMock: Mock OpenAI client with transcription capabilities
    """
    mock_client = MagicMock()
    mock_transcription = MagicMock()
    mock_transcription.text = "This is a test transcription."
    
    mock_client.audio.transcriptions.create.return_value = mock_transcription
    
    return mock_client


@pytest.fixture
def mock_openai_service(mock_openai_client):
    """
    Provide a mock OpenAI service with patched client.
    
    Yields:
        Mock: Patched OpenAI constructor
    """
    with patch("app.services.openai_service.OpenAI", return_value=mock_openai_client):
        yield mock_openai_client


@pytest.fixture
def mock_queue():
    """
    Provide a mock RQ queue for testing background jobs.
    
    Returns:
        MagicMock: Mock queue object
    """
    mock_q = MagicMock()
    mock_job = MagicMock()
    mock_job.id = "test-job-123"
    mock_job.get_status.return_value = "queued"
    mock_q.enqueue.return_value = mock_job
    return mock_q


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_job_data():
    """
    Provide sample job data for testing.
    
    Returns:
        dict: Sample job data
    """
    return {
        "id": "test-job-123",
        "status": "pending",
        "audio_file_path": "/tmp/test_audio.mp3",
        "transcript": None,
        "error_message": None,
    }


@pytest.fixture
def sample_lexicon_data():
    """
    Provide sample lexicon data for testing.
    
    Returns:
        dict: Sample lexicon terms
    """
    return {
        "mri": "MRI",
        "ct": "CT",
        "xray": "X-ray",
        "ecg": "ECG"
    }


@pytest.fixture
def sample_transcription_text():
    """
    Provide sample transcription text for testing.
    
    Returns:
        str: Sample transcription text
    """
    return "The patient underwent an mri scan and ct scan. The results show normal findings."


# ============================================================================
# Async Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for async tests.
    
    Yields:
        asyncio.AbstractEventLoop: Event loop
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Settings Override Fixtures
# ============================================================================

@pytest.fixture
def test_settings():
    """
    Provide test settings with safe defaults.
    
    Returns:
        Settings: Test settings instance
    """
    return Settings(
        DATABASE_URL="sqlite:///:memory:",
        REDIS_URL="redis://localhost:6379/15",
        OPENAI_API_KEY="test-api-key-12345",
        OPENAI_MODEL="whisper-1",
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        AUDIO_STORAGE_PATH="/tmp/test_audio",
        AUDIO_RETENTION_HOURS=1,
        CLEANUP_INTERVAL_MINUTES=5,
    )


@pytest.fixture
def override_settings(test_settings):
    """
    Override application settings with test settings.
    
    Yields:
        Settings: Test settings
    """
    with patch("app.config.settings.get_settings", return_value=test_settings):
        yield test_settings
