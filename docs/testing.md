# Testing Guide

This document provides comprehensive information about testing the Speech-to-Text Transcription Service.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Fixtures](#fixtures)
- [Test Environment](#test-environment)
- [Coverage](#coverage)
- [CI/CD Integration](#cicd-integration)
- [Best Practices](#best-practices)

## Overview

The project uses **pytest** as the primary testing framework with support for:

- Unit tests (fast, isolated, no external dependencies)
- Integration tests (database, Redis, API endpoints)
- Async tests (for asynchronous code)
- Coverage reporting (minimum 80% threshold)
- Parallel test execution (for faster runs)

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures for all tests
├── __init__.py
├── unit/                    # Unit tests (no external dependencies)
│   ├── __init__.py
│   ├── test_postprocessing_service.py
│   ├── test_numeral_handler.py
│   └── test_text_cleanup.py
├── integration/             # Integration tests (require external services)
│   └── __init__.py
└── test_openai_service.py   # Service-level tests
```

### Test Types

**Unit Tests** (`@pytest.mark.unit`)
- Test individual functions and classes in isolation
- Use mocks for external dependencies
- Should be fast (< 1 second per test)
- No database, Redis, or API calls

**Integration Tests** (`@pytest.mark.integration`)
- Test interaction between components
- May require database, Redis, or external services
- Test API endpoints end-to-end
- Can be slower (< 5 seconds per test)

## Running Tests

### Quick Start

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration
```

### Using the Test Script

The project includes a comprehensive test runner script:

```bash
# Make the script executable (first time only)
chmod +x scripts/run_tests.sh

# Run all tests
./scripts/run_tests.sh

# Run with coverage report
./scripts/run_tests.sh --coverage --html

# Run only unit tests
./scripts/run_tests.sh --unit

# Run only integration tests
./scripts/run_tests.sh --integration

# Run tests in parallel (faster)
./scripts/run_tests.sh --fast

# Run in Docker environment
./scripts/run_tests.sh --docker

# CI mode (strict coverage, XML output)
./scripts/run_tests.sh --ci
```

### Docker Environment

Run tests in an isolated Docker environment:

```bash
# Using docker-compose directly
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Using the test script
./scripts/run_tests.sh --docker

# Clean up after tests
docker-compose -f docker-compose.test.yml down -v
```

## Writing Tests

### Basic Test Example

```python
import pytest
from app.services.example_service import process_data

@pytest.mark.unit
def test_process_data():
    """Test data processing with valid input."""
    result = process_data("test input")
    assert result == "expected output"
```

### Using Fixtures

```python
import pytest

@pytest.mark.unit
def test_with_database(db_session):
    """Test that uses database fixture."""
    from app.models import Job
    
    # Create test data
    job = Job(id="test-123", status="pending")
    db_session.add(job)
    db_session.commit()
    
    # Query and verify
    queried_job = db_session.query(Job).filter_by(id="test-123").first()
    assert queried_job is not None
    assert queried_job.status == "pending"
```

### API Testing

```python
import pytest

@pytest.mark.integration
@pytest.mark.api
def test_health_endpoint(api_client):
    """Test health check endpoint."""
    response = api_client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
```

### Async Testing

```python
import pytest

@pytest.mark.asyncio
@pytest.mark.unit
async def test_async_function():
    """Test asynchronous function."""
    result = await some_async_function()
    assert result is not None
```

### Mocking External Services

```python
import pytest
from unittest.mock import patch, MagicMock

@pytest.mark.unit
def test_with_mock_openai(mock_openai_service):
    """Test with mocked OpenAI service."""
    from app.services.transcription import transcribe_audio
    
    # Mock is already set up by fixture
    result = transcribe_audio("test.mp3")
    
    assert result == "This is a test transcription."
```

## Fixtures

The project provides comprehensive fixtures in `tests/conftest.py`:

### Database Fixtures

- **`test_engine`**: SQLAlchemy engine for tests (SQLite in-memory)
- **`db_session`**: Database session with automatic rollback after each test
- **`override_get_db`**: Override FastAPI dependency for test database

### Redis Fixtures

- **`redis_available`**: Check if Redis is available for testing
- **`redis_client`**: Real Redis client (database 15) with cleanup
- **`mock_redis_client`**: Mock Redis client for unit tests

### API Fixtures

- **`test_client`**: FastAPI TestClient with database override
- **`api_client`**: Alias for test_client
- **`auth_headers`**: Authentication headers for API tests
- **`admin_auth_headers`**: Admin authentication headers

### Mock Service Fixtures

- **`mock_openai_client`**: Mock OpenAI client
- **`mock_openai_service`**: Mock OpenAI service with patched client
- **`mock_queue`**: Mock RQ queue for background jobs

### Data Fixtures

- **`sample_job_data`**: Sample job data for testing
- **`sample_lexicon_data`**: Sample lexicon terms
- **`sample_transcription_text`**: Sample transcription text

### Settings Fixtures

- **`test_settings`**: Test settings with safe defaults
- **`override_settings`**: Override application settings with test settings

### Example Usage

```python
@pytest.mark.integration
def test_create_job(db_session, sample_job_data):
    """Test job creation with fixtures."""
    from app.models import Job
    
    job = Job(**sample_job_data)
    db_session.add(job)
    db_session.commit()
    
    assert job.id == sample_job_data["id"]
```

## Test Environment

### Environment Variables

Test environment variables are defined in `.env.test`:

```bash
# Load test environment
export $(grep -v '^#' .env.test | xargs)

# Or let pytest/script handle it automatically
```

Key test settings:
- `TESTING=true`: Flag indicating test environment
- `DATABASE_URL=sqlite:///:memory:`: In-memory SQLite for fast tests
- `REDIS_URL=redis://localhost:6379/15`: Isolated Redis database
- `OPENAI_API_KEY=test-api-key-*`: Mock API key (not real)

### Isolated Test Services

**PostgreSQL Test Database**
```bash
# Start test database
docker-compose -f docker-compose.test.yml up -d test-db

# Access: postgresql://test_user:test_password@localhost:5433/test_transcription
```

**Redis Test Instance**
```bash
# Start test Redis
docker-compose -f docker-compose.test.yml up -d test-redis

# Access: redis://localhost:6380/0
```

## Coverage

### Coverage Configuration

Coverage is configured in `.coveragerc` and `pytest.ini`:

- **Minimum threshold**: 80% overall coverage
- **Branch coverage**: Enabled
- **Excluded patterns**: Tests, migrations, `__init__.py` files

### Viewing Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Coverage Output

```
---------- coverage: platform linux, python 3.11 -----------
Name                                  Stmts   Miss  Cover   Missing
-------------------------------------------------------------------
app/main.py                             45      2    96%   32-33
app/services/transcription.py          78      5    94%   45, 67-70
app/models/job.py                       25      0   100%
-------------------------------------------------------------------
TOTAL                                  148      7    95%
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test_password
          POSTGRES_USER: test_user
          POSTGRES_DB: test_transcription
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -e .[dev]
      
      - name: Run tests
        run: |
          ./scripts/run_tests.sh --ci
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### GitLab CI Example

```yaml
test:
  stage: test
  image: python:3.11
  
  services:
    - postgres:15
    - redis:7-alpine
  
  variables:
    POSTGRES_DB: test_transcription
    POSTGRES_USER: test_user
    POSTGRES_PASSWORD: test_password
    DATABASE_URL: postgresql://test_user:test_password@postgres:5432/test_transcription
    REDIS_URL: redis://redis:6379/0
  
  before_script:
    - pip install -e .[dev]
  
  script:
    - ./scripts/run_tests.sh --ci
  
  coverage: '/TOTAL.*\s+(\d+%)$/'
  
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

## Best Practices

### 1. Test Isolation

- Each test should be independent and not rely on other tests
- Use fixtures for setup and teardown
- Database sessions automatically rollback after each test

### 2. Test Naming

```python
# Good: Descriptive test names
def test_user_creation_with_valid_data():
    pass

def test_user_creation_fails_with_duplicate_email():
    pass

# Bad: Vague test names
def test_user1():
    pass

def test_user2():
    pass
```

### 3. Arrange-Act-Assert Pattern

```python
def test_process_data():
    # Arrange: Set up test data
    input_data = "test input"
    expected_output = "TEST INPUT"
    
    # Act: Execute the function
    result = process_data(input_data)
    
    # Assert: Verify the result
    assert result == expected_output
```

### 4. Use Markers

```python
@pytest.mark.unit
def test_unit_function():
    pass

@pytest.mark.integration
@pytest.mark.database
def test_database_integration():
    pass

@pytest.mark.slow
def test_expensive_operation():
    pass
```

### 5. Mock External Dependencies

```python
@pytest.mark.unit
def test_with_mock():
    with patch('app.services.external_api.call') as mock_call:
        mock_call.return_value = {"status": "success"}
        result = my_function()
        assert result["status"] == "success"
        mock_call.assert_called_once()
```

### 6. Parametrize Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
    ("", ""),
])
def test_uppercase(input, expected):
    assert input.upper() == expected
```

### 7. Test Edge Cases

```python
def test_division():
    assert divide(10, 2) == 5
    
    # Test edge cases
    assert divide(0, 5) == 0
    
    with pytest.raises(ZeroDivisionError):
        divide(5, 0)
```

### 8. Keep Tests Fast

- Unit tests should run in milliseconds
- Use mocks for external services
- Use in-memory databases for tests
- Run slow tests separately with markers

### 9. Document Test Purpose

```python
def test_lexicon_replacement():
    """
    Test that lexicon replacement correctly replaces terms
    while preserving case and handling word boundaries.
    
    This ensures medical terms like 'mri' are properly
    capitalized to 'MRI' in transcription output.
    """
    pass
```

### 10. Clean Test Data

```python
@pytest.fixture
def test_data(db_session):
    """Create test data and ensure cleanup."""
    job = Job(id="test-123")
    db_session.add(job)
    db_session.commit()
    
    yield job
    
    # Cleanup happens automatically via db_session rollback
```

## Adding New Tests

### 1. Unit Test Example

Create `tests/unit/test_new_feature.py`:

```python
import pytest
from app.services.new_feature import process_feature

@pytest.mark.unit
def test_process_feature_with_valid_input():
    """Test feature processing with valid input."""
    result = process_feature("valid input")
    assert result is not None
    assert result.status == "success"

@pytest.mark.unit
def test_process_feature_with_invalid_input():
    """Test feature processing handles invalid input."""
    with pytest.raises(ValueError):
        process_feature(None)
```

### 2. Integration Test Example

Create `tests/integration/test_api_endpoints.py`:

```python
import pytest

@pytest.mark.integration
@pytest.mark.api
def test_create_job_endpoint(api_client, auth_headers):
    """Test job creation via API."""
    response = api_client.post(
        "/api/jobs",
        json={"audio_file": "test.mp3"},
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "job_id" in data
```

### 3. Database Test Example

```python
import pytest
from app.models import Job

@pytest.mark.integration
@pytest.mark.database
def test_job_model_crud(db_session):
    """Test Job model CRUD operations."""
    # Create
    job = Job(id="test-123", status="pending")
    db_session.add(job)
    db_session.commit()
    
    # Read
    queried = db_session.query(Job).filter_by(id="test-123").first()
    assert queried.status == "pending"
    
    # Update
    queried.status = "completed"
    db_session.commit()
    
    # Delete
    db_session.delete(queried)
    db_session.commit()
```

## Troubleshooting

### Tests Fail to Connect to Database

```bash
# Check if PostgreSQL is running
docker-compose -f docker-compose.test.yml ps

# Start test database
docker-compose -f docker-compose.test.yml up -d test-db
```

### Tests Fail to Connect to Redis

```bash
# Check if Redis is running
redis-cli -h localhost -p 6379 ping

# Start Redis
docker-compose -f docker-compose.test.yml up -d test-redis
```

### Import Errors

```bash
# Ensure package is installed in development mode
pip install -e .[dev]

# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Slow Tests

```bash
# Run with duration report to identify slow tests
pytest --durations=10

# Run tests in parallel
pytest -n auto
```

### Coverage Not Meeting Threshold

```bash
# Generate detailed coverage report
pytest --cov=app --cov-report=term-missing

# View HTML report to identify uncovered lines
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)
