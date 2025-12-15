# Quick Start Guide: Using Test Fixtures

This guide will get you started with using the test fixtures in under 5 minutes.

## Setup

### 1. Generate Audio Files (Optional)

```bash
cd tests/fixtures/audio
python generate_test_audio.py
```

This creates minimal test audio files. These are auto-generated if missing, so this step is optional.

### 2. Run Example Tests

```bash
# From project root
pytest tests/test_fixtures_example.py -v
```

This verifies all fixtures are working correctly.

## Common Usage Patterns

### Pattern 1: Simple Database Test

```python
def test_create_job(test_db_session):
    """Test with isolated database session."""
    from app.models.job import Job
    
    job = Job(job_id="test-123", status="pending")
    test_db_session.add(job)
    test_db_session.commit()
    
    retrieved = test_db_session.query(Job).filter_by(job_id="test-123").first()
    assert retrieved.status == "pending"
```

### Pattern 2: Using Factory Functions

```python
def test_with_factory():
    """Test using factory to generate test data."""
    from tests.utils.factories import create_completed_job
    
    job_data = create_completed_job(
        language="en",
        audio_format="wav"
    )
    
    assert job_data["status"] == "completed"
    assert job_data["transcription_text"] is not None
```

### Pattern 3: Mocking OpenAI

```python
def test_with_openai_mock(mock_openai_success):
    """Test using OpenAI mock."""
    result = mock_openai_success.transcribe_audio(
        audio_file_path="/tmp/test.wav",
        language="en"
    )
    
    assert isinstance(result, str)
    assert len(result) > 0
```

### Pattern 4: Mocking Redis Queue

```python
def test_with_queue_mock(mock_redis_queue):
    """Test using Redis queue mock."""
    job = mock_redis_queue.enqueue(
        lambda: "test",
        job_id="test-job-123"
    )
    
    assert job.get_status() == "queued"
    assert len(mock_redis_queue) == 1
```

### Pattern 5: Using Sample Files

```python
def test_with_audio_file(sample_wav_file):
    """Test with sample audio file."""
    assert sample_wav_file.exists()
    
    with open(sample_wav_file, 'rb') as f:
        data = f.read()
        assert len(data) > 0
```

### Pattern 6: Pre-Seeded Database

```python
def test_with_seeded_db(seed_test_database):
    """Test with fully populated database."""
    from app.models.job import Job
    
    jobs = seed_test_database.query(Job).all()
    assert len(jobs) >= 5  # Database is pre-populated
    
    completed_jobs = seed_test_database.query(Job).filter_by(status="completed").all()
    assert len(completed_jobs) > 0
```

## Available Fixtures Quick Reference

### Database Fixtures
- `test_db_session` - Clean database session
- `db_with_jobs` - Database with jobs
- `seed_test_database` - Fully seeded database

### Mock Services
- `mock_openai_success` - Successful OpenAI transcription
- `mock_openai_rate_limit` - Rate limit error
- `mock_redis_queue` - Empty Redis queue
- `mock_redis_queue_with_jobs` - Queue with test jobs

### Sample Files
- `sample_wav_file` - WAV audio file
- `sample_mp3_file` - MP3 audio file
- `sample_m4a_file` - M4A audio file
- `lexicon_data` - Medical terminology data

### Sample Data
- `sample_pending_job` - Pending job data
- `sample_completed_job` - Completed job data
- `sample_failed_job` - Failed job data

## Factory Functions Quick Reference

```python
from tests.utils.factories import (
    # Jobs
    create_pending_job,
    create_completed_job,
    create_failed_job,
    
    # Feedback
    create_pending_feedback,
    create_approved_feedback,
    
    # API Keys
    create_active_api_key,
    create_admin_api_key,
    
    # Lexicon Terms
    create_radiology_term,
    create_cardiology_term,
)
```

## Writing Your First Test

### Step 1: Create Test File

```bash
touch tests/unit/test_my_feature.py
```

### Step 2: Write Test

```python
"""Tests for my feature."""
import pytest

def test_my_feature(test_db_session):
    """Test my feature with database."""
    from app.models.job import Job
    from tests.utils.factories import create_completed_job
    
    # Create test data using factory
    job_data = create_completed_job()
    
    # Create model instance
    job = Job(**job_data)
    test_db_session.add(job)
    test_db_session.commit()
    
    # Test your feature
    result = my_feature(job)
    assert result is not None
```

### Step 3: Run Test

```bash
pytest tests/unit/test_my_feature.py -v
```

## Testing Tips

### Tip 1: Use Appropriate Fixtures

- **Unit tests:** Use `test_db_session`, factories, and mocks
- **Integration tests:** Use `seed_test_database` and `integration_test_setup`

### Tip 2: Combine Fixtures

```python
def test_complex_scenario(test_db_session, mock_openai_success, sample_wav_file):
    """Multiple fixtures can be combined."""
    # Use all fixtures together
    pass
```

### Tip 3: Create Custom Fixtures

```python
@pytest.fixture
def custom_test_data(test_db_session):
    """Your custom fixture building on base fixtures."""
    from tests.utils.factories import create_completed_job
    
    job_data = create_completed_job()
    # Customize as needed
    
    return job_data
```

## Common Patterns

### Testing Error Handling

```python
def test_error_handling(mock_openai_rate_limit):
    """Test handling of OpenAI rate limit."""
    from tests.mocks.openai_mock import MockRateLimitError
    
    with pytest.raises(MockRateLimitError):
        mock_openai_rate_limit.transcribe_audio("/tmp/test.wav")
```

### Testing Database Queries

```python
def test_query(db_with_jobs):
    """Test database queries."""
    from app.models.job import Job
    
    pending_jobs = db_with_jobs.query(Job).filter_by(status="pending").all()
    assert len(pending_jobs) > 0
```

### Testing File Processing

```python
def test_file_processing(sample_wav_file, temp_storage_dir):
    """Test processing audio file."""
    import shutil
    
    # Copy to temp storage
    dest = temp_storage_dir / "test.wav"
    shutil.copy(sample_wav_file, dest)
    
    # Process file
    result = process_audio(dest)
    assert result is not None
```

## Troubleshooting

### Issue: Audio files not found

**Solution:** Generate them:
```bash
cd tests/fixtures/audio
python generate_test_audio.py
```

Or let fixtures auto-generate them on first use.

### Issue: Database conflicts

**Solution:** Ensure you're using `test_db_session` fixture, which auto-rolls back.

### Issue: Import errors

**Solution:** Check you're importing from correct paths:
```python
from tests.utils.factories import create_job
from tests.mocks.openai_mock import get_success_mock
```

## Next Steps

1. **Read Full Documentation:** See `tests/fixtures/README.md`
2. **Explore Examples:** Check `tests/test_fixtures_example.py`
3. **View Implementation:** See `tests/FIXTURES_IMPLEMENTATION_SUMMARY.md`
4. **Write Tests:** Start writing tests for your features!

## Getting Help

- **Fixtures Documentation:** `tests/fixtures/README.md`
- **Example Tests:** `tests/test_fixtures_example.py`
- **Mock Services:** `tests/mocks/openai_mock.py`, `tests/mocks/redis_mock.py`
- **Factories:** `tests/utils/factories.py`
- **Main Fixtures:** `tests/conftest.py`
