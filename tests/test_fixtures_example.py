"""
Example tests demonstrating fixture usage.

This file shows how to use the various fixtures and mocks
provided in conftest.py for testing.
"""
import pytest
from pathlib import Path


# ============================================================================
# Database Fixture Examples
# ============================================================================

def test_database_session(test_db_session):
    """Test using isolated database session."""
    from app.models.job import Job
    
    # Create a test job
    job = Job(job_id="test-123", status="pending")
    test_db_session.add(job)
    test_db_session.commit()
    
    # Verify it was created
    retrieved = test_db_session.query(Job).filter_by(job_id="test-123").first()
    assert retrieved is not None
    assert retrieved.status == "pending"


def test_database_with_jobs(db_with_jobs):
    """Test using pre-populated database with jobs."""
    from app.models.job import Job
    
    # Query existing jobs
    jobs = db_with_jobs.query(Job).all()
    assert len(jobs) >= 5  # We added 5 jobs in the fixture
    
    # Check job statuses
    statuses = [job.status for job in jobs]
    assert "pending" in statuses
    assert "completed" in statuses
    assert "failed" in statuses


def test_seeded_database(seed_test_database):
    """Test using fully seeded database."""
    from app.models.job import Job
    from app.models.api_key import ApiKey
    from app.models.lexicon_term import LexiconTerm
    
    # Verify all entity types exist
    jobs = seed_test_database.query(Job).all()
    api_keys = seed_test_database.query(ApiKey).all()
    terms = seed_test_database.query(LexiconTerm).all()
    
    assert len(jobs) > 0
    assert len(api_keys) > 0
    assert len(terms) > 0


# ============================================================================
# Mock Service Examples
# ============================================================================

def test_mock_openai_success(mock_openai_success):
    """Test using mock OpenAI service."""
    result = mock_openai_success.transcribe_audio(
        audio_file_path="/tmp/test.wav",
        language="en"
    )
    
    assert isinstance(result, str)
    assert len(result) > 0


def test_mock_openai_rate_limit(mock_openai_rate_limit):
    """Test handling OpenAI rate limit."""
    from tests.mocks.openai_mock import MockRateLimitError
    
    with pytest.raises(MockRateLimitError):
        mock_openai_rate_limit.transcribe_audio(
            audio_file_path="/tmp/test.wav"
        )


def test_mock_redis_queue(mock_redis_queue):
    """Test using mock Redis queue."""
    # Enqueue a job
    job = mock_redis_queue.enqueue(
        lambda: "test",
        job_id="test-job-123"
    )
    
    assert job.id == "test-job-123"
    assert job.get_status() == "queued"
    
    # Verify queue length
    assert len(mock_redis_queue) == 1


def test_mock_redis_queue_with_jobs(mock_redis_queue_with_jobs):
    """Test using pre-populated mock queue."""
    # Queue already has jobs
    assert len(mock_redis_queue_with_jobs) > 0
    
    # Get all jobs
    jobs = mock_redis_queue_with_jobs.get_jobs()
    assert len(jobs) == 5


# ============================================================================
# File Fixture Examples
# ============================================================================

def test_sample_wav_file(sample_wav_file):
    """Test using sample WAV file."""
    assert sample_wav_file.exists()
    assert sample_wav_file.suffix == ".wav"
    
    # Verify it's readable
    with open(sample_wav_file, 'rb') as f:
        data = f.read()
        assert len(data) > 0


def test_sample_mp3_file(sample_mp3_file):
    """Test using sample MP3 file."""
    assert sample_mp3_file.exists()
    assert sample_mp3_file.suffix == ".mp3"


def test_sample_m4a_file(sample_m4a_file):
    """Test using sample M4A file."""
    assert sample_m4a_file.exists()
    assert sample_m4a_file.suffix == ".m4a"


def test_temp_audio_file(temp_audio_file):
    """Test using temporary audio file."""
    assert temp_audio_file.exists()
    
    # This file is automatically cleaned up after the test
    with open(temp_audio_file, 'rb') as f:
        data = f.read()
        assert len(data) > 0


def test_lexicon_data(lexicon_data):
    """Test loading lexicon data."""
    assert "radiology" in lexicon_data
    assert "cardiology" in lexicon_data
    assert "general" in lexicon_data
    
    # Check structure
    radiology = lexicon_data["radiology"]
    assert len(radiology) > 0
    assert "term" in radiology[0]
    assert "replacement" in radiology[0]


def test_radiology_lexicon(radiology_lexicon):
    """Test using radiology lexicon."""
    assert len(radiology_lexicon) == 20
    
    # Check for specific terms
    terms = [item["term"] for item in radiology_lexicon]
    assert "mri" in terms
    assert "ct scan" in terms


# ============================================================================
# Factory Examples
# ============================================================================

def test_job_factory():
    """Test using job factory."""
    from tests.utils.factories import create_pending_job, create_completed_job
    
    # Create pending job
    pending = create_pending_job()
    assert pending["status"] == "pending"
    assert "job_id" in pending
    
    # Create completed job
    completed = create_completed_job()
    assert completed["status"] == "completed"
    assert completed["transcription_text"] is not None


def test_feedback_factory():
    """Test using feedback factory."""
    from tests.utils.factories import create_pending_feedback
    
    feedback = create_pending_feedback(
        job_id=1,
        original_text="Original",
        corrected_text="Corrected"
    )
    
    assert feedback["status"] == "pending"
    assert feedback["job_id"] == 1
    assert feedback["original_text"] == "Original"


def test_api_key_factory():
    """Test using API key factory."""
    from tests.utils.factories import create_active_api_key
    
    api_key = create_active_api_key(
        project_name="Test Project",
        rate_limit=100
    )
    
    assert api_key["is_active"] is True
    assert api_key["rate_limit"] == 100
    assert api_key["project_name"] == "Test Project"


def test_lexicon_term_factory():
    """Test using lexicon term factory."""
    from tests.utils.factories import create_radiology_term
    
    term = create_radiology_term("mri", "MRI")
    
    assert term["lexicon_id"] == "radiology"
    assert term["term"] == "mri"
    assert term["replacement"] == "MRI"


# ============================================================================
# Sample Data Fixture Examples
# ============================================================================

def test_sample_job_data(sample_job_data):
    """Test using sample job data."""
    assert "job_id" in sample_job_data
    assert "status" in sample_job_data
    assert sample_job_data["status"] == "completed"


def test_sample_pending_job(sample_pending_job):
    """Test using sample pending job."""
    assert sample_pending_job["status"] == "pending"


def test_sample_completed_job(sample_completed_job):
    """Test using sample completed job."""
    assert sample_completed_job["status"] == "completed"
    assert sample_completed_job["transcription_text"] is not None


def test_sample_failed_job(sample_failed_job):
    """Test using sample failed job."""
    assert sample_failed_job["status"] == "failed"
    assert sample_failed_job["error_message"] is not None


# ============================================================================
# Integration Test Example
# ============================================================================

def test_integration_setup(integration_test_setup):
    """Test using complete integration setup."""
    setup = integration_test_setup
    
    # Verify all components are available
    assert "db" in setup
    assert "queue" in setup
    assert "openai" in setup
    
    # Database session is ready
    from app.models.job import Job
    job = Job(job_id="int-test-123", status="pending")
    setup["db"].add(job)
    setup["db"].commit()
    
    # Queue is ready
    queued_job = setup["queue"].enqueue(lambda: "test", job_id="queue-test")
    assert queued_job is not None
    
    # OpenAI mock is ready
    result = setup["openai"].transcribe_audio(audio_file_path="/tmp/test.wav")
    assert isinstance(result, str)


# ============================================================================
# Composable Fixture Example
# ============================================================================

@pytest.fixture
def job_with_completed_transcription(test_db_session):
    """
    Example of a composable fixture that builds on base fixtures.
    
    Creates a completed job with realistic transcription data.
    """
    from app.models.job import Job
    from tests.utils.factories import create_completed_job
    
    job_data = create_completed_job(
        transcription_text="Patient underwent MRI scan. Results show normal findings.",
        audio_format="wav",
        language="en"
    )
    
    job = Job(**job_data)
    test_db_session.add(job)
    test_db_session.commit()
    
    return job


def test_custom_fixture(job_with_completed_transcription):
    """Test using custom composable fixture."""
    job = job_with_completed_transcription
    
    assert job.status == "completed"
    assert "MRI" in job.transcription_text
    assert job.audio_format == "wav"
