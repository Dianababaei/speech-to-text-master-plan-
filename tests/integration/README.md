# Integration Tests

This directory contains integration tests for the Speech-to-Text Transcription Service API. These tests validate complete workflows using real database and Redis instances in an isolated test environment.

## Overview

The integration tests cover the following workflows:

1. **Transcription Workflow** (`test_transcription_workflow.py`)
   - Audio file upload and job creation
   - Job status polling
   - Transcription results verification
   - Multiple audio formats (MP3, WAV, M4A)
   - Lexicon selection via header/parameter

2. **Lexicon Management** (`test_lexicon_management.py`)
   - CRUD operations on lexicon terms
   - Soft delete functionality
   - Lexicon listing and filtering
   - Term application in transcriptions

3. **Feedback Workflow** (`test_feedback_workflow.py`)
   - Feedback submission
   - Listing with filters (status, lexicon, date range)
   - Status updates (approve/reject)
   - Status transition validation

4. **Authentication & Rate Limiting** (`test_auth_and_rate_limiting.py`)
   - API key validation (valid, invalid, inactive)
   - Admin privilege enforcement
   - Rate limit enforcement
   - Error responses (401, 403, 404, 429)

## Setup

### Prerequisites

- Python 3.9+
- Docker and Docker Compose (for isolated test environment)
- PostgreSQL and Redis (can use docker-compose.test.yml)

### Installation

1. Install test dependencies:
   ```bash
   pip install -e ".[dev]"
   # or
   pip install pytest pytest-asyncio httpx
   ```

2. Set up test environment variables (optional):
   ```bash
   export TEST_DATABASE_URL="postgresql://test_user:test_password@localhost:5433/test_transcription"
   export TEST_REDIS_URL="redis://localhost:6380/0"
   ```

## Running Tests

### Using Docker Compose (Recommended)

Start the test database and Redis:

```bash
# Start test services
docker-compose -f docker-compose.test.yml up -d

# Wait for services to be ready
sleep 5

# Run integration tests
pytest tests/integration/ -v

# Stop test services
docker-compose -f docker-compose.test.yml down
```

### Using Local Services

If you have PostgreSQL and Redis running locally:

```bash
# Set environment variables
export TEST_DATABASE_URL="postgresql://user:password@localhost:5432/test_db"
export TEST_REDIS_URL="redis://localhost:6379/1"

# Run tests
pytest tests/integration/ -v
```

### Run Specific Test Files

```bash
# Run only transcription tests
pytest tests/integration/test_transcription_workflow.py -v

# Run only authentication tests
pytest tests/integration/test_auth_and_rate_limiting.py -v

# Run specific test class
pytest tests/integration/test_feedback_workflow.py::TestFeedbackSubmission -v

# Run specific test
pytest tests/integration/test_transcription_workflow.py::TestTranscriptionUpload::test_upload_audio_creates_job -v
```

### Run with Coverage

```bash
pytest tests/integration/ --cov=app --cov-report=html
```

## Test Configuration

### Fixtures

Common fixtures are defined in `conftest.py`:

- `test_db`: Provides a clean database session for each test
- `test_client`: FastAPI test client with dependency overrides
- `api_key`: Regular API key for testing
- `admin_api_key`: Admin API key for admin endpoints
- `sample_lexicon_terms`: Pre-populated lexicon terms
- `sample_job`: Sample transcription job
- `mock_openai_transcribe`: Mocked OpenAI API client

### Test Isolation

Each test:
- Uses a separate database transaction (rolled back after test)
- Cleans Redis database before and after
- Has isolated audio file storage
- Mocks external OpenAI API calls

## Test Markers

Tests are marked with `@pytest.mark.integration`:

```bash
# Run only integration tests
pytest -m integration

# Exclude integration tests
pytest -m "not integration"
```

## Continuous Integration

For CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Start test services
  run: docker-compose -f docker-compose.test.yml up -d

- name: Wait for services
  run: sleep 10

- name: Run integration tests
  run: pytest tests/integration/ -v --junit-xml=test-results.xml

- name: Stop test services
  run: docker-compose -f docker-compose.test.yml down
  if: always()
```

## Troubleshooting

### Database Connection Issues

If tests fail to connect to the database:

1. Check that PostgreSQL is running:
   ```bash
   docker-compose -f docker-compose.test.yml ps
   ```

2. Verify connection string:
   ```bash
   psql postgresql://test_user:test_password@localhost:5433/test_transcription
   ```

3. Check logs:
   ```bash
   docker-compose -f docker-compose.test.yml logs test_db
   ```

### Redis Connection Issues

If Redis connection fails:

1. Check Redis is running:
   ```bash
   docker-compose -f docker-compose.test.yml ps test_redis
   ```

2. Test connection:
   ```bash
   redis-cli -h localhost -p 6380 ping
   ```

### Port Conflicts

If test services fail to start due to port conflicts:

1. Stop conflicting services or change ports in `docker-compose.test.yml`
2. Default test ports: PostgreSQL (5433), Redis (6380)

### Mock Issues

If OpenAI API mocks aren't working:

1. Check that `mock_openai_transcribe` fixture is used in test
2. Verify mock configuration in `conftest.py`
3. Ensure OpenAI service code is mockable

## Test Data

Test data is:
- **Automatically created** by fixtures in `conftest.py`
- **Cleaned up** after each test (transaction rollback)
- **Isolated** between tests

Sample data includes:
- API keys (regular and admin)
- Lexicon terms (multiple lexicons)
- Jobs (pending, completed, failed)
- Feedback records (various statuses)

## Writing New Tests

When adding new integration tests:

1. Use the `@pytest.mark.integration` marker
2. Leverage existing fixtures from `conftest.py`
3. Follow the existing test structure and naming
4. Mock external API calls (OpenAI)
5. Ensure tests are idempotent and isolated
6. Document any new fixtures or helpers

Example:

```python
@pytest.mark.integration
class TestNewFeature:
    """Tests for new feature."""
    
    def test_new_functionality(self, test_client, api_key):
        """Test new functionality."""
        response = test_client.get(
            "/new-endpoint",
            headers={"X-API-Key": api_key.key}
        )
        
        assert response.status_code == 200
```

## Known Limitations

1. **Rate Limiting**: Some rate limiting tests may skip if rate limiting is not fully implemented
2. **Async Processing**: Tests don't wait for actual background job processing (uses mocks)
3. **Audio Processing**: Real audio transcription is mocked (doesn't call OpenAI API)
4. **Time-dependent Tests**: Some tests that require time delays are skipped for speed

## Contributing

When contributing integration tests:

1. Ensure all tests pass locally
2. Add tests for new API endpoints
3. Update this README if adding new test files
4. Follow existing patterns and conventions
5. Keep tests fast and isolated
