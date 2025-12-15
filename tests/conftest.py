"""
Shared pytest fixtures for testing.

This module provides reusable fixtures for:
- Database setup and teardown
- Mock services (OpenAI, Redis)
- Sample data (jobs, feedback, API keys, lexicon terms)
- Test utilities
"""
import pytest
import json
import tempfile
from pathlib import Path
from typing import Generator, Dict, Any, List
from unittest.mock import MagicMock, patch
from datetime import datetime

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Import models
from app.models.api_key import Base
from app.models.job import Job
from app.models.feedback import Feedback
from app.models.api_key import ApiKey
from app.models.lexicon_term import LexiconTerm

# Import mocks
from tests.mocks.openai_mock import (
    create_mock_openai_service,
    get_success_mock,
    SAMPLE_RESPONSES
)
from tests.mocks.redis_mock import (
    create_mock_redis,
    create_mock_queue,
    create_mock_job
)

# Import factories
from tests.utils.factories import (
    create_pending_job,
    create_completed_job,
    create_failed_job,
    create_pending_feedback,
    create_active_api_key,
    create_radiology_term,
    create_cardiology_term,
    create_general_term,
    generate_job_id,
    generate_api_key,
    generate_hash
)


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_db_engine():
    """
    Create a test database engine using SQLite in-memory.
    
    This is shared across the entire test session for performance.
    """
    # Create in-memory SQLite database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Set to True for SQL debugging
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine) -> Generator[Session, None, None]:
    """
    Create a test database session with automatic rollback.
    
    Each test gets a fresh session that is automatically rolled back
    after the test completes, ensuring test isolation.
    """
    # Create a new session for this test
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine
    )
    session = TestingSessionLocal()
    
    # Enable nested transactions for SQLite
    session.begin_nested()
    
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            session.begin_nested()
    
    yield session
    
    # Rollback and close
    session.rollback()
    session.close()


@pytest.fixture
def db_with_jobs(test_db_session) -> Session:
    """Database session pre-populated with test jobs."""
    jobs_data = [
        create_pending_job(),
        create_completed_job(),
        create_failed_job(),
        create_pending_job(language="fa"),
        create_completed_job(audio_format="wav"),
    ]
    
    for job_data in jobs_data:
        job = Job(**job_data)
        test_db_session.add(job)
    
    test_db_session.commit()
    return test_db_session


@pytest.fixture
def db_with_api_keys(test_db_session) -> Session:
    """Database session pre-populated with test API keys."""
    keys_data = [
        create_active_api_key(project_name="Test Project 1", rate_limit=100),
        create_active_api_key(project_name="Test Project 2", rate_limit=50),
        create_active_api_key(project_name="Admin Project", is_admin=True, rate_limit=1000),
    ]
    
    for key_data in keys_data:
        api_key = ApiKey(**key_data)
        test_db_session.add(api_key)
    
    test_db_session.commit()
    return test_db_session


@pytest.fixture
def db_with_lexicon_terms(test_db_session) -> Session:
    """Database session pre-populated with lexicon terms."""
    terms_data = [
        create_radiology_term("mri", "MRI"),
        create_radiology_term("ct scan", "CT scan"),
        create_radiology_term("xray", "X-ray"),
        create_cardiology_term("ecg", "ECG"),
        create_cardiology_term("ekg", "EKG"),
        create_general_term("bp", "BP"),
    ]
    
    for term_data in terms_data:
        term = LexiconTerm(**term_data)
        test_db_session.add(term)
    
    test_db_session.commit()
    return test_db_session


@pytest.fixture
def db_with_feedback(test_db_session, db_with_jobs) -> Session:
    """Database session with jobs and feedback records."""
    # Get job IDs
    jobs = test_db_session.query(Job).all()
    
    for job in jobs[:3]:  # Add feedback for first 3 jobs
        feedback_data = create_pending_feedback(
            job_id=job.id,
            original_text="Original text from transcription",
            corrected_text="Corrected text by reviewer"
        )
        feedback = Feedback(**feedback_data)
        test_db_session.add(feedback)
    
    test_db_session.commit()
    return test_db_session


@pytest.fixture
def seed_test_database(test_db_session) -> Session:
    """
    Fully seeded test database with all entity types.
    
    Includes:
    - API keys (active, inactive, admin)
    - Jobs (pending, processing, completed, failed)
    - Lexicon terms (radiology, cardiology, general)
    - Feedback records (pending, approved, rejected)
    """
    # Create API keys
    api_keys_data = [
        create_active_api_key(project_name="Standard Project", rate_limit=100),
        create_active_api_key(project_name="Premium Project", rate_limit=500),
        create_active_api_key(project_name="Admin Project", is_admin=True, rate_limit=1000),
    ]
    
    for key_data in api_keys_data:
        api_key = ApiKey(**key_data)
        test_db_session.add(api_key)
    test_db_session.commit()
    
    # Create jobs
    jobs_data = [
        create_pending_job(audio_format="wav"),
        create_pending_job(audio_format="mp3", language="fa"),
        create_completed_job(audio_format="wav", transcription_text="English medical report"),
        create_completed_job(audio_format="mp3", language="fa", transcription_text="Persian text"),
        create_failed_job(error_message="OpenAI API rate limit exceeded"),
    ]
    
    for job_data in jobs_data:
        job = Job(**job_data)
        test_db_session.add(job)
    test_db_session.commit()
    
    # Create lexicon terms
    lexicon_terms_data = [
        # Radiology
        create_radiology_term("mri", "MRI"),
        create_radiology_term("ct scan", "CT scan"),
        create_radiology_term("xray", "X-ray"),
        create_radiology_term("ultrasound", "ultrasound"),
        # Cardiology
        create_cardiology_term("ecg", "ECG"),
        create_cardiology_term("ekg", "EKG"),
        create_cardiology_term("echocardiogram", "echocardiogram"),
        # General
        create_general_term("bp", "BP"),
        create_general_term("hr", "HR"),
        create_general_term("prn", "PRN"),
    ]
    
    for term_data in lexicon_terms_data:
        term = LexiconTerm(**term_data)
        test_db_session.add(term)
    test_db_session.commit()
    
    # Create feedback for completed jobs
    completed_jobs = test_db_session.query(Job).filter_by(status="completed").all()
    for job in completed_jobs:
        feedback_data = create_pending_feedback(
            job_id=job.id,
            original_text=job.transcription_text or "Original",
            corrected_text="Corrected medical terminology"
        )
        feedback = Feedback(**feedback_data)
        test_db_session.add(feedback)
    test_db_session.commit()
    
    return test_db_session


# ============================================================================
# Mock Service Fixtures
# ============================================================================

@pytest.fixture
def mock_openai_success():
    """Mock OpenAI service that returns successful transcription."""
    return get_success_mock(response_type="english")


@pytest.fixture
def mock_openai_persian():
    """Mock OpenAI service that returns Persian transcription."""
    return get_success_mock(response_type="persian")


@pytest.fixture
def mock_openai_rate_limit():
    """Mock OpenAI service that raises rate limit error."""
    from tests.mocks.openai_mock import get_rate_limit_mock
    return get_rate_limit_mock()


@pytest.fixture
def mock_openai_api_error():
    """Mock OpenAI service that raises API error."""
    from tests.mocks.openai_mock import get_api_error_mock
    return get_api_error_mock()


@pytest.fixture
def mock_redis_connection():
    """Mock Redis connection."""
    return create_mock_redis()


@pytest.fixture
def mock_redis_queue():
    """Mock RQ queue."""
    return create_mock_queue()


@pytest.fixture
def mock_redis_queue_with_jobs():
    """Mock RQ queue with test jobs."""
    from tests.mocks.redis_mock import get_queue_with_jobs
    return get_queue_with_jobs(count=5)


# ============================================================================
# File Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Get path to fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def audio_fixtures_dir(fixtures_dir) -> Path:
    """Get path to audio fixtures directory."""
    return fixtures_dir / "audio"


@pytest.fixture
def sample_wav_file(audio_fixtures_dir) -> Path:
    """Path to sample WAV file."""
    wav_path = audio_fixtures_dir / "sample_english.wav"
    
    # Generate if doesn't exist
    if not wav_path.exists():
        import wave
        import struct
        
        with wave.open(str(wav_path), 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            for _ in range(1600):  # 0.1 seconds
                wav_file.writeframes(struct.pack('<h', 0))
    
    return wav_path


@pytest.fixture
def sample_mp3_file(audio_fixtures_dir) -> Path:
    """Path to sample MP3 file."""
    mp3_path = audio_fixtures_dir / "sample_persian.mp3"
    
    # Generate if doesn't exist
    if not mp3_path.exists():
        # Minimal MP3 header
        mp3_data = bytearray([
            0x49, 0x44, 0x33, 0x03, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00,
            0xFF, 0xFB, 0x90, 0x00,
        ] + [0x00] * 100)
        mp3_path.write_bytes(bytes(mp3_data))
    
    return mp3_path


@pytest.fixture
def sample_m4a_file(audio_fixtures_dir) -> Path:
    """Path to sample M4A file."""
    m4a_path = audio_fixtures_dir / "sample_medical.m4a"
    
    # Generate if doesn't exist
    if not m4a_path.exists():
        # Minimal M4A/MP4 container
        ftyp = bytearray([
            0x00, 0x00, 0x00, 0x20,
            0x66, 0x74, 0x79, 0x70,
            0x4D, 0x34, 0x41, 0x20,
            0x00, 0x00, 0x00, 0x00,
            0x4D, 0x34, 0x41, 0x20,
            0x69, 0x73, 0x6F, 0x6D,
            0x00, 0x00, 0x00, 0x00,
        ])
        mdat = bytearray([
            0x00, 0x00, 0x00, 0x08,
            0x6D, 0x64, 0x61, 0x74,
        ])
        m4a_path.write_bytes(bytes(ftyp + mdat))
    
    return m4a_path


@pytest.fixture
def temp_audio_file(tmp_path) -> Path:
    """Create a temporary audio file for testing."""
    import wave
    import struct
    
    audio_path = tmp_path / "temp_test.wav"
    
    with wave.open(str(audio_path), 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        for _ in range(1600):  # 0.1 seconds of silence
            wav_file.writeframes(struct.pack('<h', 0))
    
    return audio_path


@pytest.fixture(scope="session")
def lexicon_data(fixtures_dir) -> Dict[str, List[Dict[str, str]]]:
    """Load lexicon test data from JSON file."""
    lexicon_file = fixtures_dir / "lexicons.json"
    with open(lexicon_file) as f:
        return json.load(f)


@pytest.fixture
def radiology_lexicon(lexicon_data) -> List[Dict[str, str]]:
    """Get radiology lexicon terms."""
    return lexicon_data["radiology"]


@pytest.fixture
def cardiology_lexicon(lexicon_data) -> List[Dict[str, str]]:
    """Get cardiology lexicon terms."""
    return lexicon_data["cardiology"]


@pytest.fixture
def general_lexicon(lexicon_data) -> List[Dict[str, str]]:
    """Get general lexicon terms."""
    return lexicon_data["general"]


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_job_data() -> Dict[str, Any]:
    """Sample job data for testing."""
    return create_completed_job()


@pytest.fixture
def sample_pending_job() -> Dict[str, Any]:
    """Sample pending job."""
    return create_pending_job()


@pytest.fixture
def sample_completed_job() -> Dict[str, Any]:
    """Sample completed job."""
    return create_completed_job(
        transcription_text="Patient presents with chest pain and shortness of breath."
    )


@pytest.fixture
def sample_failed_job() -> Dict[str, Any]:
    """Sample failed job."""
    return create_failed_job(error_message="OpenAI API timeout")


@pytest.fixture
def sample_feedback_data() -> Dict[str, Any]:
    """Sample feedback data."""
    return create_pending_feedback(
        job_id=1,
        original_text="Patient has mri results",
        corrected_text="Patient has MRI results"
    )


@pytest.fixture
def sample_api_key_data() -> Dict[str, Any]:
    """Sample API key data."""
    return create_active_api_key()


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def mock_datetime():
    """Mock datetime for testing time-dependent code."""
    fixed_datetime = datetime(2024, 1, 15, 12, 0, 0)
    
    with patch('app.models.job.datetime') as mock_dt:
        mock_dt.utcnow.return_value = fixed_datetime
        mock_dt.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        yield mock_dt


@pytest.fixture
def temp_storage_dir(tmp_path) -> Path:
    """Create temporary storage directory for audio files."""
    storage_dir = tmp_path / "audio_storage"
    storage_dir.mkdir(exist_ok=True)
    return storage_dir


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables before each test."""
    import os
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


# ============================================================================
# Integration Test Fixtures
# ============================================================================

@pytest.fixture
def integration_test_setup(test_db_session, mock_redis_queue, mock_openai_success):
    """
    Complete setup for integration tests.
    
    Provides:
    - Test database session
    - Mock Redis queue
    - Mock OpenAI service
    """
    return {
        "db": test_db_session,
        "queue": mock_redis_queue,
        "openai": mock_openai_success
    }


@pytest.fixture
def mock_app_dependencies(test_db_session, mock_redis_queue):
    """Mock all application dependencies for testing."""
    with patch('app.database.get_db') as mock_get_db, \
         patch('app.services.queue.get_queue') as mock_get_queue, \
         patch('app.services.openai_service.transcribe_audio') as mock_transcribe:
        
        # Configure mocks
        mock_get_db.return_value = test_db_session
        mock_get_queue.return_value = mock_redis_queue
        mock_transcribe.return_value = "Mocked transcription result"
        
        yield {
            "db": mock_get_db,
            "queue": mock_get_queue,
            "transcribe": mock_transcribe
        }


# ============================================================================
# Marker Fixtures
# ============================================================================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "external: marks tests that require external services"
    )


# ============================================================================
# Test Data Cleanup
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_test_files(tmp_path):
    """Automatically cleanup temporary test files after each test."""
    yield
    # Cleanup happens automatically with tmp_path
