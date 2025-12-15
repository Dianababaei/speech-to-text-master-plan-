"""
Integration test fixtures and configuration.

Provides shared fixtures for database setup, test client, API keys,
and test data cleanup.
"""
import os
import tempfile
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
import redis
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

from app.database import get_db
from app.main import app
from app.models import Base, ApiKey, Job, LexiconTerm, Feedback
from app.config.settings import Settings, get_settings


# Test database configuration
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://test_user:test_password@localhost:5433/test_transcription"
)
TEST_REDIS_URL = os.getenv(
    "TEST_REDIS_URL",
    "redis://localhost:6380/0"
)


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Fixture to provide test-specific settings."""
    settings = Settings()
    settings.DATABASE_URL = TEST_DATABASE_URL
    settings.REDIS_URL = TEST_REDIS_URL
    settings.OPENAI_API_KEY = "test-api-key"
    settings.DEBUG = True
    settings.AUDIO_STORAGE_PATH = tempfile.mkdtemp()
    return settings


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine."""
    engine = create_engine(
        TEST_DATABASE_URL,
        pool_pre_ping=True,
        echo=False
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Drop all tables after tests
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(test_engine) -> Generator[Session, None, None]:
    """
    Provide a clean database session for each test.
    
    Uses transaction rollback for fast cleanup between tests.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    
    yield session
    
    # Rollback transaction to clean up test data
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def test_redis():
    """Provide a Redis connection for testing."""
    r = redis.from_url(TEST_REDIS_URL)
    
    # Clear the test Redis database before each test
    r.flushdb()
    
    yield r
    
    # Clean up after test
    r.flushdb()
    r.close()


@pytest.fixture(scope="function")
def test_client(test_db: Session, test_settings: Settings) -> TestClient:
    """
    Provide a FastAPI test client with test database.
    
    Overrides the database dependency to use the test database.
    """
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    def override_get_settings():
        return test_settings
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_settings] = override_get_settings
    
    client = TestClient(app)
    
    yield client
    
    # Clean up dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def api_key(test_db: Session) -> ApiKey:
    """Create a test API key for authentication."""
    key = ApiKey(
        key="test-api-key-12345",
        project_name="test-project",
        description="Test API key",
        is_active=True,
        is_admin=False,
        rate_limit=100
    )
    test_db.add(key)
    test_db.commit()
    test_db.refresh(key)
    return key


@pytest.fixture(scope="function")
def admin_api_key(test_db: Session) -> ApiKey:
    """Create a test admin API key for admin endpoints."""
    key = ApiKey(
        key="admin-api-key-12345",
        project_name="admin-project",
        description="Test admin API key",
        is_active=True,
        is_admin=True,
        rate_limit=100
    )
    test_db.add(key)
    test_db.commit()
    test_db.refresh(key)
    return key


@pytest.fixture(scope="function")
def inactive_api_key(test_db: Session) -> ApiKey:
    """Create an inactive API key for negative testing."""
    key = ApiKey(
        key="inactive-api-key-12345",
        project_name="inactive-project",
        description="Inactive test API key",
        is_active=False,
        is_admin=False,
        rate_limit=100
    )
    test_db.add(key)
    test_db.commit()
    test_db.refresh(key)
    return key


@pytest.fixture(scope="function")
def sample_lexicon_terms(test_db: Session) -> list[LexiconTerm]:
    """Create sample lexicon terms for testing."""
    terms = [
        LexiconTerm(
            lexicon_id="radiology",
            term="mri",
            replacement="MRI",
            is_active=True
        ),
        LexiconTerm(
            lexicon_id="radiology",
            term="ct scan",
            replacement="CT scan",
            is_active=True
        ),
        LexiconTerm(
            lexicon_id="cardiology",
            term="ecg",
            replacement="ECG",
            is_active=True
        ),
        LexiconTerm(
            lexicon_id="radiology",
            term="xray",
            replacement="X-ray",
            is_active=False  # Soft deleted
        ),
    ]
    
    for term in terms:
        test_db.add(term)
    
    test_db.commit()
    
    for term in terms:
        test_db.refresh(term)
    
    return terms


@pytest.fixture(scope="function")
def sample_job(test_db: Session, api_key: ApiKey) -> Job:
    """Create a sample transcription job for testing."""
    job = Job(
        job_id="123e4567-e89b-12d3-a456-426614174000",
        status="completed",
        audio_filename="test.mp3",
        audio_format="mp3",
        audio_storage_path="/tmp/test.mp3",
        transcription_text="The patient needs an mri scan",
        api_key_id=api_key.id
    )
    test_db.add(job)
    test_db.commit()
    test_db.refresh(job)
    return job


@pytest.fixture(scope="function")
def mock_openai_transcribe():
    """
    Mock OpenAI API transcription calls.
    
    Returns a mock that can be configured per test.
    """
    with patch('app.services.openai_service.OpenAI') as mock:
        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.return_value = MagicMock(
            text="This is a test transcription"
        )
        mock.return_value = mock_client
        yield mock_client


@pytest.fixture(scope="function")
def sample_audio_files():
    """
    Create temporary audio files for testing different formats.
    
    Returns a dictionary with file paths for different formats.
    """
    files = {}
    
    # Create temporary audio files with minimal valid headers
    formats = {
        'mp3': b'\xFF\xFB\x90\x00' + b'\x00' * 100,  # Minimal MP3 header
        'wav': b'RIFF' + b'\x00' * 4 + b'WAVE' + b'\x00' * 100,  # Minimal WAV header
        'm4a': b'\x00\x00\x00\x20ftyp' + b'\x00' * 100,  # Minimal M4A header
    }
    
    for format_name, content in formats.items():
        temp_file = tempfile.NamedTemporaryFile(
            suffix=f'.{format_name}',
            delete=False,
            mode='wb'
        )
        temp_file.write(content)
        temp_file.close()
        files[format_name] = temp_file.name
    
    yield files
    
    # Cleanup
    for file_path in files.values():
        try:
            os.unlink(file_path)
        except OSError:
            pass


@pytest.fixture(scope="function")
def clean_audio_storage(test_settings: Settings):
    """Clean up audio storage directory after each test."""
    yield
    
    # Cleanup audio storage
    import shutil
    if os.path.exists(test_settings.AUDIO_STORAGE_PATH):
        shutil.rmtree(test_settings.AUDIO_STORAGE_PATH, ignore_errors=True)
    os.makedirs(test_settings.AUDIO_STORAGE_PATH, exist_ok=True)
