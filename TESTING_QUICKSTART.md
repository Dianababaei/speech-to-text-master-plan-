# Testing Quick Start Guide

Get up and running with tests in 5 minutes.

## Installation

```bash
# Install all dependencies including test tools
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install
```

## Run Tests

```bash
# Run all tests
make test

# Run with coverage report
make test-coverage

# View HTML coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## Common Test Commands

```bash
# Unit tests only (fast)
pytest -m unit

# Integration tests only
pytest -m integration

# Specific test file
pytest tests/unit/test_example.py

# Specific test function
pytest tests/unit/test_example.py::test_function_name

# Run in parallel (faster)
pytest -n auto

# Verbose output
pytest -vv

# Show print statements
pytest -s
```

## Writing Your First Test

### 1. Unit Test (No Dependencies)

```python
# tests/unit/test_my_feature.py
import pytest

@pytest.mark.unit
def test_my_function():
    """Test description."""
    result = my_function("input")
    assert result == "expected"
```

### 2. Database Test

```python
# tests/integration/test_database.py
import pytest
from app.models import Job

@pytest.mark.integration
@pytest.mark.database
def test_create_job(db_session):
    """Test job creation."""
    job = Job(id="test-123", status="pending")
    db_session.add(job)
    db_session.commit()
    
    assert job.id == "test-123"
```

### 3. API Test

```python
# tests/integration/test_api.py
import pytest

@pytest.mark.integration
@pytest.mark.api
def test_endpoint(api_client, auth_headers):
    """Test API endpoint."""
    response = api_client.get("/api/endpoint", headers=auth_headers)
    assert response.status_code == 200
```

## Available Fixtures

Use these in your tests by adding them as parameters:

- `db_session` - Database session with rollback
- `api_client` - FastAPI test client
- `redis_client` - Real Redis client (DB 15)
- `mock_redis_client` - Mock Redis client
- `mock_openai_client` - Mock OpenAI client
- `auth_headers` - Auth headers for API tests
- `sample_job_data` - Sample job data
- `sample_lexicon_data` - Sample lexicon terms

## Pre-Commit Hooks

Pre-commit hooks run automatically before each commit:

```bash
# Install hooks (one time)
pre-commit install

# Run manually
pre-commit run --all-files

# Skip hooks for a commit (not recommended)
git commit --no-verify
```

## Docker Testing

```bash
# Run tests in Docker
./scripts/run_tests.sh --docker

# Or manually
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
docker-compose -f docker-compose.test.yml down -v
```

## Troubleshooting

### Import Errors
```bash
pip install -e .[dev]
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Redis Not Available
```bash
# Skip Redis tests
pytest -m "not redis"

# Or start Redis
docker-compose -f docker-compose.test.yml up -d test-redis
```

### Tests Too Slow
```bash
# Run in parallel
pytest -n auto

# Run only fast tests
pytest -m "unit"
```

## More Information

- **Full Guide**: [docs/testing.md](docs/testing.md)
- **Pipeline Details**: [TESTING_PIPELINE.md](TESTING_PIPELINE.md)
- **Example Tests**: [tests/unit/test_fixtures_example.py](tests/unit/test_fixtures_example.py)

## Cheat Sheet

```bash
# Quick Commands
make test              # All tests
make test-unit         # Unit only
make test-coverage     # With coverage
make test-fast         # Parallel

# Pytest
pytest -m unit         # Unit tests
pytest -m integration  # Integration tests
pytest -k test_name    # By name
pytest -vv             # Verbose
pytest --lf            # Last failed
pytest --durations=10  # Slowest tests

# Coverage
pytest --cov=app --cov-report=html
open htmlcov/index.html

# Pre-commit
pre-commit run --all-files
pre-commit autoupdate

# Clean up
make clean
make clean-test
```

Happy testing! 🧪✨
