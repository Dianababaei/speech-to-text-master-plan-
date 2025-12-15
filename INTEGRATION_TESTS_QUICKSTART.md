# Integration Tests - Quick Start Guide

## 🚀 TL;DR - Run Tests Now

```bash
# Option 1: Using Makefile (Recommended)
make test-integration

# Option 2: Using shell script
chmod +x run_integration_tests.sh
./run_integration_tests.sh

# Option 3: Manual
docker-compose -f docker-compose.test.yml up -d
sleep 5
pytest tests/integration/ -v
docker-compose -f docker-compose.test.yml down
```

## 📋 Prerequisites

- Python 3.9+
- Docker and Docker Compose
- Pytest installed (`pip install pytest pytest-asyncio`)

## 🎯 What Gets Tested?

| Test Suite | Tests | What It Covers |
|------------|-------|----------------|
| **Transcription Workflow** | 25+ | Audio upload, job creation, status polling, format validation |
| **Lexicon Management** | 20+ | CRUD operations, soft delete, filtering, term application |
| **Feedback Workflow** | 25+ | Submit, list, filter, approve/reject, status transitions |
| **Auth & Rate Limiting** | 30+ | API keys, admin access, rate limits, error responses |

## 📦 Test Environment

The tests use **isolated** test services that won't interfere with your development environment:

- **PostgreSQL**: localhost:5433 (dev uses 5432)
- **Redis**: localhost:6380 (dev uses 6379)
- **Data**: Completely isolated, cleaned after each test

## 🔧 Setup (One-Time)

1. **Install dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

2. **Make script executable (if using shell script):**
   ```bash
   chmod +x run_integration_tests.sh
   ```

That's it! No other setup needed.

## ▶️ Running Tests

### All Integration Tests

```bash
# Recommended: Using Makefile
make test-integration

# Alternative: Using script
./run_integration_tests.sh

# Manual control
docker-compose -f docker-compose.test.yml up -d
pytest tests/integration/ -v
docker-compose -f docker-compose.test.yml down
```

### Specific Test Suites

```bash
# Start test environment once
docker-compose -f docker-compose.test.yml up -d

# Run specific suites
pytest tests/integration/test_transcription_workflow.py -v
pytest tests/integration/test_lexicon_management.py -v
pytest tests/integration/test_feedback_workflow.py -v
pytest tests/integration/test_auth_and_rate_limiting.py -v

# Stop test environment
docker-compose -f docker-compose.test.yml down
```

### With Coverage Report

```bash
make test-all
# Opens htmlcov/index.html when done
```

## 📊 Expected Output

```
✓ All tests passed!
========================= 100 passed in 30.0s =========================
```

Typical run time: **30-60 seconds**

## ❌ Troubleshooting

### Port Already in Use

If ports 5433 or 6380 are already in use:

```bash
# Check what's using the ports
lsof -i :5433
lsof -i :6380

# Stop conflicting services or change ports in docker-compose.test.yml
```

### Services Not Starting

```bash
# Check service health
docker-compose -f docker-compose.test.yml ps

# View logs
docker-compose -f docker-compose.test.yml logs

# Force cleanup and retry
docker-compose -f docker-compose.test.yml down -v
docker-compose -f docker-compose.test.yml up -d
```

### Tests Failing

```bash
# Run with more verbose output
pytest tests/integration/ -vv

# Run a single test to debug
pytest tests/integration/test_transcription_workflow.py::TestTranscriptionUpload::test_upload_audio_creates_job -vv

# Check test environment variables
echo $TEST_DATABASE_URL
echo $TEST_REDIS_URL
```

## 🔍 What Each Test File Does

| File | Purpose |
|------|---------|
| `test_transcription_workflow.py` | Tests audio upload → job creation → status → results |
| `test_lexicon_management.py` | Tests creating/updating/deleting lexicon terms |
| `test_feedback_workflow.py` | Tests submitting and managing feedback corrections |
| `test_auth_and_rate_limiting.py` | Tests API keys, permissions, and rate limits |

## 🎨 Test Markers

```bash
# Run only integration tests
pytest -m integration

# Run with specific markers
pytest -m "integration and not slow"
```

## 🔄 CI/CD Integration

For CI/CD pipelines, see `.github/workflows/integration-tests.yml.example`

## 📖 More Information

- **Full Documentation**: `tests/integration/README.md`
- **Implementation Details**: `INTEGRATION_TESTS_SUMMARY.md`
- **Fixtures & Helpers**: `tests/integration/conftest.py`

## 💡 Tips

1. **Fast iteration**: Keep test services running between test runs
   ```bash
   docker-compose -f docker-compose.test.yml up -d
   pytest tests/integration/ -v  # Run multiple times
   docker-compose -f docker-compose.test.yml down  # When done
   ```

2. **Debug specific tests**: Use `-k` flag
   ```bash
   pytest tests/integration/ -k "test_upload" -v
   ```

3. **See print statements**: Use `-s` flag
   ```bash
   pytest tests/integration/ -v -s
   ```

4. **Stop on first failure**: Use `-x` flag
   ```bash
   pytest tests/integration/ -v -x
   ```

## ✅ Success Indicators

You know the tests are working correctly when:

- ✅ All services start without errors
- ✅ Tests complete in ~30-60 seconds
- ✅ All tests pass (or expected skips for unimplemented features)
- ✅ Services shut down cleanly
- ✅ No port conflicts
- ✅ Coverage report generates successfully

## 🚨 Common Test Patterns

### Creating a Test

```python
@pytest.mark.integration
class TestMyFeature:
    def test_my_functionality(self, test_client, api_key):
        response = test_client.get(
            "/my-endpoint",
            headers={"X-API-Key": api_key.key}
        )
        assert response.status_code == 200
```

### Using Fixtures

```python
def test_with_sample_data(self, test_client, api_key, sample_job):
    # sample_job is automatically created and cleaned up
    response = test_client.get(
        f"/jobs/{sample_job.job_id}",
        headers={"X-API-Key": api_key.key}
    )
    assert response.status_code == 200
```

## 🎓 Learning Resources

1. Start with simple tests in `test_transcription_workflow.py`
2. Review fixtures in `conftest.py`
3. Check helper functions in `test_helpers.py`
4. Read inline comments in test files

---

**Happy Testing! 🎉**

For issues or questions, see the full documentation in `tests/integration/README.md`
