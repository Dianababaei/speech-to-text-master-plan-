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
Shared pytest fixtures for unit and integration tests.

Provides reusable test fixtures for database mocking, API keys, 
lexicon data, and other common test dependencies.
"""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from sqlalchemy.orm import Session


@pytest.fixture
def mock_db_session():
    """
    Mock database session for testing database operations.
    
    Returns:
        Mock: A mocked SQLAlchemy Session object with common methods
    """
    session = Mock(spec=Session)
    session.query = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    session.bulk_save_objects = Mock()
    return session


@pytest.fixture
def mock_api_key():
    """
    Mock API key object for testing authentication.
    
    Returns:
        Mock: A mocked APIKey model instance with typical attributes
    """
    api_key = Mock()
    api_key.id = "test-uuid-1234"
    api_key.key = "test-api-key-12345"
    api_key.project_name = "test-project"
    api_key.is_active = True
    api_key.is_admin = False
    api_key.rate_limit = 100
    api_key.metadata = {}
    api_key.last_used_at = None
    api_key.created_at = datetime(2024, 1, 1)
    api_key.updated_at = datetime(2024, 1, 1)
    return api_key


@pytest.fixture
def mock_admin_api_key():
    """
    Mock admin API key object for testing admin authentication.
    
    Returns:
        Mock: A mocked APIKey model instance with admin privileges
    """
    api_key = Mock()
    api_key.id = "admin-uuid-5678"
    api_key.key = "admin-api-key-67890"
    api_key.project_name = "admin-project"
    api_key.is_active = True
    api_key.is_admin = True
    api_key.rate_limit = 1000
    api_key.metadata = {"role": "admin"}
    api_key.last_used_at = None
    api_key.created_at = datetime(2024, 1, 1)
    api_key.updated_at = datetime(2024, 1, 1)
    return api_key


@pytest.fixture
def sample_lexicon_terms():
    """
    Sample lexicon terms for testing lexicon operations.
    
    Returns:
        list: List of term dictionaries with 'term' and 'replacement' keys
    """
    return [
        {"term": "MRI", "replacement": "Magnetic Resonance Imaging"},
        {"term": "CT", "replacement": "Computed Tomography"},
        {"term": "X-ray", "replacement": "Radiography"},
        {"term": "ECG", "replacement": "Electrocardiogram"},
        {"term": "BP", "replacement": "Blood Pressure"}
    ]


@pytest.fixture
def sample_persian_terms():
    """
    Sample Persian lexicon terms for testing Unicode handling.
    
    Returns:
        list: List of Persian term dictionaries
    """
    return [
        {"term": "ام آر آی", "replacement": "MRI"},
        {"term": "سی تی", "replacement": "CT"},
        {"term": "اسکن", "replacement": "scan"},
        {"term": "بیمار", "replacement": "patient"},
        {"term": "قلب", "replacement": "heart"}
    ]


@pytest.fixture
def mock_lexicon_term_model():
    """
    Mock LexiconTerm model class for database operations.
    
    Returns:
        Mock: A mocked LexiconTerm class with database fields
    """
    def create_term(**kwargs):
        term = Mock()
        term.id = kwargs.get('id', 'test-term-uuid')
        term.lexicon_id = kwargs.get('lexicon_id', 'test-lexicon')
        term.term = kwargs.get('term', 'test')
        term.replacement = kwargs.get('replacement', 'TEST')
        term.is_active = kwargs.get('is_active', True)
        term.created_at = kwargs.get('created_at', datetime.utcnow())
        term.updated_at = kwargs.get('updated_at', datetime.utcnow())
        return term
    
    return create_term


@pytest.fixture
def mock_redis_client():
    """
    Mock Redis client for testing rate limiting and caching.
    
    Returns:
        Mock: A mocked Redis client with common operations
    """
    redis_client = Mock()
    redis_client.get = Mock(return_value=None)
    redis_client.set = Mock(return_value=True)
    redis_client.setex = Mock(return_value=True)
    redis_client.incr = Mock(return_value=1)
    redis_client.expire = Mock(return_value=True)
    redis_client.delete = Mock(return_value=1)
    return redis_client


@pytest.fixture
def mock_openai_response():
    """
    Mock OpenAI API response for testing transcription.
    
    Returns:
        Mock: A mocked OpenAI transcription response
    """
    response = Mock()
    response.text = "This is a sample transcription from OpenAI."
    response.model = "whisper-1"
    response.duration = 10.5
    return response


@pytest.fixture
def sample_transcription_text():
    """
    Sample transcription text for testing post-processing.
    
    Returns:
        str: Sample English transcription text
    """
    return """
    The patient is a 45-year-old male with history of hypertension.
    MRI scan shows abnormality in L4-L5 region. CT scan was also performed.
    Blood pressure reading: 120/80 mmHg. Heart rate: 72 bpm.
    """


@pytest.fixture
def sample_persian_transcription():
    """
    Sample Persian transcription text for testing Unicode handling.
    
    Returns:
        str: Sample Persian transcription text
    """
    return """
    بیمار مرد ۴۵ ساله با سابقه فشار خون بالا.
    ام آر آی ناحیه L4-L5 آسیب نشان می‌دهد.
    فشار خون ۱۲۰/۸۰ و ضربان قلب ۷۲ است.
    """


@pytest.fixture
def text_cleanup_config():
    """
    Default configuration for text cleanup operations.
    
    Returns:
        dict: Configuration dictionary for text cleanup
    """
    return {
        "normalize_whitespace": True,
        "normalize_persian_chars": True,
        "normalize_punctuation": True,
        "remove_artifacts": True,
        "normalize_line_breaks": True,
        "unicode_normalization": "NFC"
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
def numeral_test_cases():
    """
    Test cases for numeral conversion with expected results.
    
    Returns:
        dict: Dictionary of test scenarios with input and expected output
    """
    return {
        "persian_to_english": {
            "input": "بیمار ۳۵ ساله با فشار خون ۱۲۰/۸۰",
            "expected": "بیمار 35 ساله با فشار خون 120/80"
        },
        "english_to_persian": {
            "input": "بیمار 35 ساله با فشار خون 120/80",
            "expected": "بیمار ۳۵ ساله با فشار خون ۱۲۰/۸۰"
        },
        "medical_codes": {
            "input": "مشکل در L4-L5 و T1-T2",
            "expected_english": "مشکل در L4-L5 و T1-T2",
            "expected_context_aware": "مشکل در L4-L5 و T1-T2"
        }
    }
