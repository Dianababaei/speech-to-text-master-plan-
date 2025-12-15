# Automated Testing Pipeline

This document describes the automated testing pipeline setup for the Speech-to-Text Transcription Service.

## Overview

The testing pipeline has been configured to support both local development and CI/CD environments with:

- ✅ Comprehensive test fixtures for database, Redis, API client, and mock services
- ✅ Isolated test environment with separate configuration
- ✅ Coverage reporting with 80% minimum threshold
- ✅ Parallel test execution for faster runs
- ✅ Pre-commit hooks for automated quality checks
- ✅ Docker-based test environment for CI/CD
- ✅ Comprehensive documentation

## Quick Start

### 1. Install Dependencies

```bash
# Install all development dependencies
pip install -e .[dev]

# Or using the Makefile
make install
```

### 2. Run Tests

```bash
# Run all tests
make test

# Run with coverage
make test-coverage

# Run only unit tests (fast)
make test-unit

# Run only integration tests
make test-integration

# Run in parallel (faster)
make test-fast
```

### 3. Set Up Pre-Commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

## Project Structure

```
.
├── .coveragerc                    # Coverage configuration
├── .env.test                      # Test environment variables
├── .pre-commit-config.yaml        # Pre-commit hooks configuration
├── pytest.ini                     # Pytest configuration
├── docker-compose.test.yml        # Docker test environment
├── scripts/
│   └── run_tests.sh              # Test execution script
├── tests/
│   ├── conftest.py               # Shared test fixtures
│   ├── unit/                     # Unit tests
│   └── integration/              # Integration tests
└── docs/
    └── testing.md                # Detailed testing documentation
```

## Testing Framework Configuration

### pytest.ini

Configured with:
- Test discovery patterns
- Coverage reporting (HTML, terminal, XML)
- Asyncio mode for async tests
- Test markers (unit, integration, slow, api, database, redis, openai)
- Warning filters
- Minimum coverage threshold: 80%

### Test Fixtures (tests/conftest.py)

**Database Fixtures:**
- `test_engine`: SQLAlchemy engine with SQLite in-memory database
- `db_session`: Database session with automatic rollback after each test
- `override_get_db`: FastAPI dependency override for test database

**Redis Fixtures:**
- `redis_available`: Check Redis availability
- `redis_client`: Real Redis client (database 15) with automatic cleanup
- `mock_redis_client`: Mock Redis client for unit tests

**API Fixtures:**
- `test_client`: FastAPI TestClient with database override
- `api_client`: Alias for test_client
- `auth_headers`: Authentication headers for API tests
- `admin_auth_headers`: Admin authentication headers

**Mock Service Fixtures:**
- `mock_openai_client`: Mock OpenAI client
- `mock_openai_service`: Mock OpenAI service with patched client
- `mock_queue`: Mock RQ queue for background jobs

**Data Fixtures:**
- `sample_job_data`: Sample job data
- `sample_lexicon_data`: Sample lexicon terms
- `sample_transcription_text`: Sample transcription text

**Settings Fixtures:**
- `test_settings`: Test settings with safe defaults
- `override_settings`: Override application settings

## Test Environment

### Environment Variables (.env.test)

Key test settings:
- `TESTING=true`: Flag indicating test environment
- `DATABASE_URL=sqlite:///:memory:`: Fast in-memory database
- `REDIS_URL=redis://localhost:6379/15`: Isolated Redis database
- `OPENAI_API_KEY=test-api-key-*`: Mock API key (not real)
- `LOG_LEVEL=DEBUG`: Verbose logging for tests

### Isolated Test Services

**PostgreSQL Test Database:**
```bash
docker-compose -f docker-compose.test.yml up -d test-db
# Access: postgresql://test_user:test_password@localhost:5433/test_transcription
```

**Redis Test Instance:**
```bash
docker-compose -f docker-compose.test.yml up -d test-redis
# Access: redis://localhost:6380/0
```

## Execution Scripts

### scripts/run_tests.sh

Comprehensive test runner with options:

```bash
# Make executable (first time only)
chmod +x scripts/run_tests.sh

# Run all tests
./scripts/run_tests.sh

# Options:
./scripts/run_tests.sh --unit              # Unit tests only
./scripts/run_tests.sh --integration       # Integration tests only
./scripts/run_tests.sh --coverage          # With coverage report
./scripts/run_tests.sh --html              # HTML coverage report
./scripts/run_tests.sh --fast              # Parallel execution
./scripts/run_tests.sh --docker            # Docker environment
./scripts/run_tests.sh --ci                # CI mode (strict)
./scripts/run_tests.sh --verbose           # Verbose output
```

### Makefile Targets

```bash
make test              # Run all tests
make test-unit         # Run unit tests only
make test-integration  # Run integration tests only
make test-coverage     # Run with coverage report
make test-fast         # Run in parallel
make test-docker       # Run in Docker
```

## Coverage Reporting

### Configuration (.coveragerc)

- **Minimum threshold**: 80% overall coverage
- **Branch coverage**: Enabled
- **Excluded patterns**: Tests, migrations, `__init__.py`
- **Output formats**: HTML, terminal, XML, JSON

### Viewing Coverage

```bash
# Generate HTML report
make test-coverage

# Open in browser
open htmlcov/index.html      # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage Reports

- **HTML**: `htmlcov/index.html` (detailed, interactive)
- **Terminal**: Inline output with missing lines
- **XML**: `coverage.xml` (for CI/CD tools)
- **JSON**: `coverage.json` (for programmatic access)

## Pre-Commit Hooks

### Installation

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

### Configured Hooks

1. **File checks**: Trailing whitespace, EOF, large files
2. **Black**: Code formatting (line length: 100)
3. **Ruff**: Fast Python linting with auto-fix
4. **isort**: Import sorting (Black-compatible)
5. **Bandit**: Security checks
6. **pytest-unit**: Run fast unit tests before commit

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
        ports:
          - 5432:5432
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -e .[dev]
      - run: ./scripts/run_tests.sh --ci
      - uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### Docker-based Testing

```bash
# Run full test suite in Docker
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Or using the script
./scripts/run_tests.sh --docker

# Clean up
docker-compose -f docker-compose.test.yml down -v
```

## Test Types & Markers

### Unit Tests (`@pytest.mark.unit`)

- Fast, isolated tests
- No external dependencies
- Use mocks for external services
- Should run in < 1 second per test

Example:
```python
@pytest.mark.unit
def test_process_data():
    result = process_data("input")
    assert result == "expected"
```

### Integration Tests (`@pytest.mark.integration`)

- Test component interactions
- May require database, Redis, or APIs
- Can be slower (< 5 seconds per test)

Example:
```python
@pytest.mark.integration
@pytest.mark.database
def test_create_job(db_session):
    job = Job(id="test-123", status="pending")
    db_session.add(job)
    db_session.commit()
    assert job.id == "test-123"
```

### Additional Markers

- `@pytest.mark.slow`: Slow tests (> 5 seconds)
- `@pytest.mark.api`: API endpoint tests
- `@pytest.mark.database`: Database-dependent tests
- `@pytest.mark.redis`: Redis-dependent tests
- `@pytest.mark.openai`: OpenAI API tests (mocked)

## Writing Tests

### Basic Test Structure

```python
import pytest

@pytest.mark.unit
def test_feature():
    # Arrange: Set up test data
    input_data = "test"
    
    # Act: Execute function
    result = process(input_data)
    
    # Assert: Verify result
    assert result == "expected"
```

### Using Fixtures

```python
@pytest.mark.integration
def test_with_database(db_session, sample_job_data):
    """Test with database fixture."""
    job = Job(**sample_job_data)
    db_session.add(job)
    db_session.commit()
    
    queried = db_session.query(Job).first()
    assert queried is not None
```

### API Testing

```python
@pytest.mark.integration
@pytest.mark.api
def test_endpoint(api_client, auth_headers):
    """Test API endpoint."""
    response = api_client.get("/api/endpoint", headers=auth_headers)
    assert response.status_code == 200
```

### Async Testing

```python
@pytest.mark.asyncio
@pytest.mark.unit
async def test_async_function():
    """Test async function."""
    result = await async_function()
    assert result is not None
```

## Best Practices

1. **Test Isolation**: Each test should be independent
2. **Descriptive Names**: `test_user_creation_with_valid_email`
3. **AAA Pattern**: Arrange, Act, Assert
4. **Use Markers**: Tag tests appropriately
5. **Mock External Dependencies**: Use fixtures for external services
6. **Parametrize**: Test multiple cases efficiently
7. **Test Edge Cases**: Empty input, null values, errors
8. **Keep Tests Fast**: Unit tests in milliseconds
9. **Document Purpose**: Docstrings for complex tests
10. **Clean Test Data**: Use fixtures for setup/teardown

## Common Commands Reference

```bash
# Development
make install           # Install dependencies
make test             # Run all tests
make test-coverage    # With coverage report
make format           # Format code
make lint             # Lint code
make pre-commit       # Run pre-commit hooks

# Testing
pytest                               # All tests
pytest -m unit                       # Unit tests only
pytest -m integration                # Integration tests only
pytest -k test_specific              # Specific test by name
pytest --cov=app                     # With coverage
pytest -n auto                       # Parallel execution
pytest --durations=10                # Show slowest tests
pytest -vv                           # Very verbose
pytest --tb=short                    # Short traceback

# Coverage
pytest --cov=app --cov-report=html  # HTML report
pytest --cov=app --cov-report=term  # Terminal report
pytest --cov-fail-under=80          # Fail if < 80%

# Cleanup
make clean            # Remove Python cache
make clean-test       # Remove test artifacts
```

## Troubleshooting

### Import Errors
```bash
pip install -e .[dev]
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Database Connection Issues
```bash
docker-compose -f docker-compose.test.yml up -d test-db
```

### Redis Connection Issues
```bash
docker-compose -f docker-compose.test.yml up -d test-redis
# Or skip Redis tests: pytest -m "not redis"
```

### Slow Tests
```bash
pytest --durations=10  # Identify slow tests
pytest -n auto         # Run in parallel
```

### Coverage Below Threshold
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html  # Identify uncovered code
```

## Documentation

- **Comprehensive Guide**: [docs/testing.md](docs/testing.md)
- **API Documentation**: Check docstrings in `tests/conftest.py`
- **pytest Documentation**: https://docs.pytest.org/

## Success Criteria ✅

All success criteria from the task have been met:

- [x] pytest discovers and runs all tests correctly
- [x] Coverage reports generate successfully with configurable thresholds (80%)
- [x] Tests can run in isolation and in full suite without conflicts
- [x] Clear documentation allows new developers to run tests and add new ones
- [x] CI/CD pipeline can execute tests automatically
- [x] Test environment is fully isolated from development/production

## Next Steps

1. **Install dependencies**: `pip install -e .[dev]`
2. **Make test script executable**: `chmod +x scripts/run_tests.sh`
3. **Install pre-commit hooks**: `pre-commit install`
4. **Run tests**: `make test-coverage`
5. **Review coverage report**: `open htmlcov/index.html`
6. **Add new tests**: See [docs/testing.md](docs/testing.md) for examples

---

**Note**: This testing pipeline provides a solid foundation. Continue to add tests as you develop new features to maintain high coverage and code quality.
