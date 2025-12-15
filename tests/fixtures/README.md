# Test Fixtures and Mock Data

This directory contains test fixtures, mock data, and sample files used throughout the test suite.

## Directory Structure

```
tests/fixtures/
├── audio/                  # Sample audio files for testing
│   ├── sample_english.wav  # WAV format test file
│   ├── sample_persian.mp3  # MP3 format test file
│   ├── sample_medical.m4a  # M4A format test file
│   ├── generate_test_audio.py  # Script to regenerate audio files
│   └── README.md           # Audio fixtures documentation
├── lexicons.json           # Sample lexicon terms (radiology, cardiology, general)
└── README.md               # This file
```

## Available Fixtures

### 1. Audio Files (`audio/`)

Small sample audio files in supported formats for testing file uploads and processing:

- **sample_english.wav** - Minimal WAV file (~500 bytes)
- **sample_persian.mp3** - Minimal MP3 file (~100 bytes)
- **sample_medical.m4a** - Minimal M4A file (~40 bytes)

**Usage:**
```python
from pathlib import Path

AUDIO_DIR = Path(__file__).parent / "fixtures" / "audio"

def test_upload_audio():
    audio_file = AUDIO_DIR / "sample_english.wav"
    # Use in your test...
```

**Regenerating Files:**
```bash
cd tests/fixtures/audio
python generate_test_audio.py
```

### 2. Lexicon Data (`lexicons.json`)

Sample medical terminology mappings organized by domain:

- **Radiology** - 20 imaging and diagnostic terms
- **Cardiology** - 20 heart and cardiovascular terms  
- **General** - 20 common medical abbreviations and terms

**Structure:**
```json
{
  "radiology": [
    {"term": "mri", "replacement": "MRI", "description": "..."},
    ...
  ],
  "cardiology": [...],
  "general": [...]
}
```

**Usage:**
```python
import json
from pathlib import Path

def load_lexicon_fixtures():
    fixtures_path = Path(__file__).parent / "fixtures" / "lexicons.json"
    with open(fixtures_path) as f:
        return json.load(f)

def test_lexicon_loading():
    lexicons = load_lexicon_fixtures()
    radiology_terms = lexicons["radiology"]
    assert len(radiology_terms) == 20
```

## Using Test Fixtures

### In pytest Fixtures

Fixtures can be loaded and used in pytest fixtures defined in `conftest.py`:

```python
import pytest
import json
from pathlib import Path

@pytest.fixture
def lexicon_data():
    """Load sample lexicon data."""
    fixtures_path = Path(__file__).parent / "fixtures" / "lexicons.json"
    with open(fixtures_path) as f:
        return json.load(f)

@pytest.fixture
def sample_audio_file():
    """Get path to sample WAV audio file."""
    return Path(__file__).parent / "fixtures" / "audio" / "sample_english.wav"
```

### In Test Functions

Access fixtures directly in test functions:

```python
def test_process_audio(sample_audio_file):
    """Test audio processing with fixture."""
    assert sample_audio_file.exists()
    # Process the audio file...
```

## Mock Services

In addition to file fixtures, mock services are available in `tests/mocks/`:

### OpenAI Mock (`mocks/openai_mock.py`)

Provides mock responses for OpenAI API calls:

```python
from tests.mocks.openai_mock import get_success_mock, get_rate_limit_mock

def test_transcription_success():
    mock_openai = get_success_mock(response_type="english")
    # Use mock in test...

def test_rate_limit_handling():
    mock_openai = get_rate_limit_mock()
    # Test rate limit error handling...
```

**Available mocks:**
- `get_success_mock(response_type)` - Successful transcription
- `get_rate_limit_mock()` - Rate limit error
- `get_api_error_mock()` - General API error
- `get_timeout_mock()` - Timeout error
- `get_auth_error_mock()` - Authentication error
- `get_invalid_audio_mock()` - Invalid audio format error
- `get_slow_mock(delay)` - Simulated slow response

### Redis Mock (`mocks/redis_mock.py`)

Provides in-memory mock for Redis and RQ operations:

```python
from tests.mocks.redis_mock import create_mock_queue, create_mock_job

def test_job_enqueue():
    queue = create_mock_queue()
    job = queue.enqueue(my_function, job_id="test-123")
    assert job.id == "test-123"
    assert job.get_status() == "queued"
```

**Available mocks:**
- `create_mock_redis()` - Mock Redis connection
- `create_mock_queue()` - Mock RQ queue
- `create_mock_job()` - Mock RQ job
- `get_empty_queue()` - Empty queue
- `get_queue_with_jobs(count)` - Queue with test jobs
- `get_queue_with_failed_jobs(count)` - Queue with failed jobs

## Test Data Factories

Factory functions for generating test data are available in `tests/utils/factories.py`:

### Job Factories

```python
from tests.utils.factories import (
    create_pending_job,
    create_completed_job,
    create_failed_job,
    create_multiple_jobs
)

def test_job_creation():
    pending_job = create_pending_job()
    completed_job = create_completed_job(transcription_text="Test result")
    failed_job = create_failed_job(error_message="API error")
    
    # Create multiple jobs
    jobs = create_multiple_jobs(count=10)
```

### Feedback Factories

```python
from tests.utils.factories import (
    create_pending_feedback,
    create_approved_feedback,
    create_multiple_feedback
)

def test_feedback():
    feedback = create_pending_feedback(
        job_id=1,
        original_text="Original",
        corrected_text="Corrected"
    )
```

### API Key Factories

```python
from tests.utils.factories import (
    create_active_api_key,
    create_admin_api_key,
    create_rate_limited_api_key
)

def test_api_keys():
    regular_key = create_active_api_key(rate_limit=100)
    admin_key = create_admin_api_key()
    limited_key = create_rate_limited_api_key(limit=10)
```

### Lexicon Term Factories

```python
from tests.utils.factories import (
    create_radiology_term,
    create_cardiology_term,
    create_lexicon_terms_batch
)

def test_lexicon_terms():
    term = create_radiology_term("mri", "MRI")
    
    # Create multiple terms
    terms = create_lexicon_terms_batch(
        lexicon_id="radiology",
        terms=[("ct", "CT"), ("xray", "X-ray")]
    )
```

## Database Fixtures

Database fixtures are defined in `tests/conftest.py` and provide isolated test databases:

```python
def test_with_database(test_db_session):
    """Test using isolated database session."""
    from app.models.job import Job
    
    # Create a test job
    job = Job(job_id="test-123", status="pending")
    test_db_session.add(job)
    test_db_session.commit()
    
    # Verify
    retrieved = test_db_session.query(Job).filter_by(job_id="test-123").first()
    assert retrieved is not None
```

**Available database fixtures:**
- `test_db_engine` - Test database engine (SQLite in-memory)
- `test_db_session` - Test database session (auto-rollback)
- `seed_test_data` - Pre-populated test database

## Best Practices

### 1. Use Appropriate Fixtures

- Use **file fixtures** for testing file operations
- Use **mock services** for external API calls
- Use **factories** for generating test data
- Use **database fixtures** for database-dependent tests

### 2. Keep Fixtures Fast

- Use minimal file sizes (<1KB)
- Use in-memory databases (SQLite)
- Mock external services
- Avoid network calls

### 3. Fixture Scope

Choose appropriate fixture scope:
- `function` - Fresh fixture for each test (default)
- `module` - Shared within test module
- `session` - Shared across entire test session

```python
@pytest.fixture(scope="session")
def lexicon_data():
    """Load once per test session."""
    # Load data...
```

### 4. Composable Fixtures

Build complex fixtures from simpler ones:

```python
@pytest.fixture
def completed_job_with_feedback(test_db_session):
    """Job with associated feedback."""
    job = create_completed_job()
    test_db_session.add(job)
    test_db_session.commit()
    
    feedback = create_approved_feedback(job_id=job.id)
    test_db_session.add(feedback)
    test_db_session.commit()
    
    return job, feedback
```

### 5. Cleanup

Fixtures should clean up after themselves:

```python
@pytest.fixture
def temp_audio_file(tmp_path):
    """Create temporary audio file."""
    file_path = tmp_path / "test.wav"
    # Create file...
    yield file_path
    # Cleanup happens automatically with tmp_path
```

## Extending Fixtures

### Adding New Audio Files

1. Create the audio file (keep < 1KB)
2. Place in `fixtures/audio/`
3. Document in `fixtures/audio/README.md`
4. Add fixture in `conftest.py` if needed

### Adding New Lexicon Terms

1. Edit `fixtures/lexicons.json`
2. Add terms to appropriate domain
3. Maintain consistent structure
4. Document any special cases

### Adding New Factories

1. Add factory function to `tests/utils/factories.py`
2. Follow naming convention: `create_<model>_<variant>()`
3. Use sensible defaults
4. Allow customization via kwargs
5. Document parameters and return type

## Troubleshooting

### Audio Files Missing

If audio files don't exist, regenerate them:

```bash
cd tests/fixtures/audio
python generate_test_audio.py
```

### Import Errors

Ensure test paths are correct:

```python
from pathlib import Path

# Get fixtures directory relative to current test file
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
```

### Database Conflicts

If tests fail due to database conflicts:

1. Ensure using `test_db_session` fixture
2. Check fixture scope (function vs module)
3. Verify transactions are rolled back
4. Clear any cached connections

## Additional Resources

- **Mock Services Documentation:** `tests/mocks/`
- **Factory Functions:** `tests/utils/factories.py`
- **Pytest Fixtures:** `tests/conftest.py`
- **Test Examples:** `tests/unit/` and `tests/integration/`
