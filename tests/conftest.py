"""
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
