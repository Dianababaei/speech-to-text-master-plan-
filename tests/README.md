# Test Suite Documentation

This directory contains comprehensive unit and integration tests for the Speech-to-Text service.

## Test Structure

```
tests/
├── conftest.py              # Shared pytest fixtures
├── unit/                    # Unit tests (fast, no external dependencies)
│   ├── test_auth.py        # Authentication logic tests
│   ├── test_lexicon.py     # Lexicon service tests
│   ├── test_numeral_handler.py  # Numeral conversion tests
│   ├── test_postprocessing_service.py  # Post-processing tests
│   └── test_text_cleanup.py     # Text cleanup tests
└── integration/            # Integration tests (require external services)
```

## Running Tests

### Install Dependencies

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Or install from pyproject.toml
pip install pytest pytest-asyncio
```

### Run All Tests

```bash
pytest
```

### Run Unit Tests Only

```bash
pytest -m unit
```

### Run Specific Test Categories

```bash
# Authentication tests
pytest -m auth

# Lexicon service tests
pytest -m lexicon

# Text processing tests
pytest -m text_processing

# Numeral conversion tests
pytest -m numerals
```

### Run Specific Test Files

```bash
# Test authentication
pytest tests/unit/test_auth.py

# Test lexicon service
pytest tests/unit/test_lexicon.py

# Test text cleanup
pytest tests/unit/test_text_cleanup.py
```

### Run with Coverage

```bash
# Install coverage
pip install pytest-cov

# Run tests with coverage report
pytest --cov=app --cov-report=html --cov-report=term

# View HTML coverage report
open htmlcov/index.html
```

### Run Verbose Mode

```bash
pytest -v
```

### Run with Output

```bash
pytest -s
```

## Test Markers

Tests are organized with pytest markers for easy filtering:

- `unit` - Fast unit tests with no external dependencies
- `integration` - Integration tests that may require API keys or external services
- `auth` - Authentication and authorization tests
- `lexicon` - Lexicon service and terminology tests
- `text_processing` - Text cleanup and normalization tests
- `numerals` - Numeral conversion and handling tests
- `slow` - Tests that take longer to run

## Test Coverage Goals

The test suite aims for:

- **>80% coverage** on core business logic modules
- **100% coverage** on critical authentication and security logic
- **Comprehensive edge case testing** for Unicode, Persian text, and special characters
- **Fast execution** - unit tests complete in <10 seconds

## Test Organization

### Unit Tests (`tests/unit/`)

Unit tests focus on individual functions and modules in isolation:

#### `test_auth.py`
- API key validation logic
- Admin privilege checking
- Error handling for missing/invalid keys
- Active/inactive key status handling

**Key test classes:**
- `TestGetApiKey` - API key validation
- `TestGetAdminApiKey` - Admin authentication
- `TestAuthenticationFlow` - Complete auth flows
- `TestEdgeCases` - Boundary conditions

#### `test_lexicon.py`
- Term validation for import operations
- Duplicate detection (case-insensitive)
- Database import/export operations
- Conflict detection with existing terms

**Key test classes:**
- `TestValidateTermsForImport` - Import validation logic
- `TestImportTermsToDatabase` - Database import operations
- `TestExportTermsFromDatabase` - Database export operations
- `TestEdgeCases` - Unicode, special characters, long strings

#### `test_numeral_handler.py`
- Persian ↔ English numeral conversion
- Medical term preservation (vertebral levels, measurements)
- Context-aware numeral processing
- All strategy options (english/persian/preserve/context_aware)

**Key test classes:**
- `TestBasicNumeralConversion` - Simple conversions
- `TestMedicalTermDetection` - Medical code detection
- `TestEnglishStrategy` - English numeral strategy
- `TestPersianStrategy` - Persian numeral strategy
- `TestContextAwareStrategy` - Context-aware strategy
- `TestRealWorldScenarios` - Real medical reports

#### `test_text_cleanup.py`
- Whitespace normalization
- Persian character normalization
- Punctuation consistency
- Transcription artifact removal
- Unicode normalization

**Key test classes:**
- `TestWhitespaceNormalization` - Whitespace handling
- `TestPersianCharacterNormalization` - Persian text normalization
- `TestPunctuationNormalization` - Punctuation handling
- `TestTranscriptionArtifactRemoval` - Artifact removal
- `TestUnicodeNormalization` - Unicode handling
- `TestComprehensiveCleanup` - Full pipeline tests

#### `test_postprocessing_service.py`
- Lexicon-based text replacement
- Case preservation logic
- Longest-match-first strategy
- Persian/English code-switching

**Key test classes:**
- `TestCasePreservation` - Case handling
- `TestSimpleReplacements` - Basic replacements
- `TestWholeWordMatching` - Word boundary matching
- `TestLongestMatchFirst` - Longest match strategy
- `TestPersianText` - Persian text handling

## Shared Fixtures (`conftest.py`)

Common test fixtures available to all tests:

### Database Fixtures
- `mock_db_session` - Mocked SQLAlchemy session
- `mock_lexicon_term_model` - Mocked LexiconTerm model

### Authentication Fixtures
- `mock_api_key` - Regular API key
- `mock_admin_api_key` - Admin API key

### Test Data Fixtures
- `sample_lexicon_terms` - Sample English terms
- `sample_persian_terms` - Sample Persian terms
- `sample_transcription_text` - Sample English transcription
- `sample_persian_transcription` - Sample Persian transcription
- `numeral_test_cases` - Numeral conversion test cases

### External Service Mocks
- `mock_redis_client` - Mocked Redis client
- `mock_openai_response` - Mocked OpenAI API response

## Mocking Strategy

Tests use comprehensive mocking to avoid external dependencies:

### Database Operations
```python
# Database queries are mocked
mock_query = Mock()
mock_query.filter.return_value.all.return_value = []
mock_db_session.query.return_value = mock_query
```

### Redis Operations
```python
# Redis client operations are mocked
mock_redis.get.return_value = None
mock_redis.set.return_value = True
```

### OpenAI API
```python
# OpenAI responses are mocked
mock_response = Mock()
mock_response.text = "Sample transcription"
```

## Writing New Tests

### Test Structure Template

```python
import pytest
from unittest.mock import Mock, patch

# Mark tests appropriately
pytestmark = [pytest.mark.unit, pytest.mark.your_marker]

class TestYourFeature:
    """Test description."""
    
    def test_happy_path(self, mock_db_session):
        """Test normal successful operation."""
        # Arrange
        input_data = "test input"
        
        # Act
        result = your_function(input_data)
        
        # Assert
        assert result == expected_output
    
    def test_edge_case(self):
        """Test boundary condition."""
        # Test implementation
        pass
    
    def test_error_handling(self):
        """Test error scenario."""
        with pytest.raises(ExpectedException):
            your_function(invalid_input)
```

### Best Practices

1. **Use descriptive test names** - Test names should describe what is being tested
2. **Follow AAA pattern** - Arrange, Act, Assert
3. **Test one thing per test** - Each test should verify one specific behavior
4. **Mock external dependencies** - Use fixtures and mocks to isolate units
5. **Test edge cases** - Empty strings, None values, Unicode, very long inputs
6. **Test error handling** - Verify proper exception handling
7. **Use fixtures** - Leverage shared fixtures from conftest.py
8. **Add markers** - Tag tests appropriately for filtering

## Continuous Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# Example CI configuration
- name: Run tests
  run: |
    pip install -e ".[dev]"
    pytest --cov=app --cov-report=xml
```

## Test Performance

Unit tests are optimized for speed:

- **No network calls** - All external services are mocked
- **No database connections** - Database operations are mocked
- **Fast fixtures** - Lightweight mock objects
- **Parallel execution ready** - Tests are independent

Target performance:
- Unit tests: <10 seconds total
- Individual test: <100ms average

## Troubleshooting

### Tests Not Found

```bash
# Ensure pytest can find the tests
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### Import Errors

```bash
# Install package in editable mode
pip install -e .
```

### Async Test Warnings

```bash
# Install pytest-asyncio
pip install pytest-asyncio
```

### Missing Fixtures

Check that `conftest.py` is in the correct location and fixtures are properly defined.

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure tests cover happy path, edge cases, and error scenarios
3. Mock all external dependencies
4. Add appropriate test markers
5. Update this README if adding new test categories
6. Aim for >80% code coverage on new code

## Related Documentation

- [Main README](../README.md) - Project overview
- [API Documentation](../docs/) - API endpoint documentation
- [Implementation Docs](../IMPLEMENTATION.md) - Implementation details
