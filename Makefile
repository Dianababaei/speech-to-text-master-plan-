.PHONY: help install migrate migrate-down migrate-create migrate-history migrate-current db-up db-down db-reset clean test test-unit test-integration test-coverage test-fast test-docker

# Default target
help:
	@echo "Available commands:"
	@echo ""
	@echo "Installation:"
	@echo "  make install         - Install Python dependencies"
	@echo "  make install            - Install Python dependencies"
	@echo "  make migrate            - Run all migrations (upgrade to head)"
	@echo "  make migrate-down       - Rollback all migrations"
	@echo "  make migrate-create     - Create a new migration (use MSG='description')"
	@echo "  make migrate-history    - Show migration history"
	@echo "  make migrate-current    - Show current migration version"
	@echo "  make db-up              - Start PostgreSQL with Docker"
	@echo "  make db-down            - Stop PostgreSQL Docker container"
	@echo "  make db-reset           - Reset database (down + up migrations)"
	@echo "  make test               - Run all tests"
	@echo "  make test-unit          - Run unit tests only"
	@echo "  make test-integration   - Run integration tests with test environment"
	@echo "  make test-all           - Run all tests with coverage"
	@echo "  make clean              - Remove Python cache files"
	@echo ""
	@echo "Testing:"
	@echo "  make test            - Run all tests"
	@echo "  make test-unit       - Run unit tests only"
	@echo "  make test-integration- Run integration tests only"
	@echo "  make test-coverage   - Run tests with coverage report"
	@echo "  make test-auth       - Run authentication tests"
	@echo "  make test-lexicon    - Run lexicon service tests"
	@echo "  make test-text       - Run text processing tests"
	@echo "  make test-numerals   - Run numeral conversion tests"
	@echo ""
	@echo "Development:"
	@echo "  make install         - Install Python dependencies"
	@echo "  make install-dev     - Install dev dependencies"
	@echo ""
	@echo "Database:"
	@echo "  make migrate         - Run all migrations (upgrade to head)"
	@echo "  make migrate-down    - Rollback all migrations"
	@echo "  make migrate-create  - Create a new migration (use MSG='description')"
	@echo "  make migrate-history - Show migration history"
	@echo "  make migrate-current - Show current migration version"
	@echo "  make db-up           - Start PostgreSQL with Docker"
	@echo "  make db-down         - Stop PostgreSQL Docker container"
	@echo "  make db-reset        - Reset database (down + up migrations)"
	@echo ""
	@echo "Testing:"
	@echo "  make test            - Run all tests"
	@echo "  make test-unit       - Run only unit tests"
	@echo "  make test-integration - Run only integration tests"
	@echo "  make test-coverage   - Run tests with coverage report"
	@echo "  make test-fast       - Run tests in parallel"
	@echo "  make test-docker     - Run tests in Docker environment"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint            - Run linters (ruff)"
	@echo "  make format          - Format code (black, isort)"
	@echo "  make pre-commit      - Run pre-commit hooks"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean           - Remove Python cache files"
	@echo "  make clean-test      - Remove test artifacts"

# Install dependencies
install:
	pip install -r requirements.txt

# Install dev dependencies including test tools
install-dev:
	pip install -e ".[dev]"

# Run all tests
test:
	@echo "Running all tests..."
	pytest

# Run unit tests only
test-unit:
	@echo "Running unit tests..."
	pytest -m unit

# Run integration tests only
test-integration:
	@echo "Running integration tests..."
	pytest -m integration

# Run tests with coverage report
test-coverage:
	@echo "Running tests with coverage..."
	pytest --cov=app --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated: htmlcov/index.html"

# Run authentication tests
test-auth:
	@echo "Running authentication tests..."
	pytest -m auth -v

# Run lexicon service tests
test-lexicon:
	@echo "Running lexicon service tests..."
	pytest -m lexicon -v

# Run text processing tests
test-text:
	@echo "Running text processing tests..."
	pytest -m text_processing -v

# Run numeral conversion tests
test-numerals:
	@echo "Running numeral conversion tests..."
	pytest -m numerals -v

# Run tests in verbose mode
test-verbose:
	@echo "Running tests in verbose mode..."
	pytest -v

# Run migrations
migrate:
	alembic upgrade head

# Rollback all migrations
migrate-down:
	alembic downgrade base

# Create a new migration
migrate-create:
	@if [ -z "$(MSG)" ]; then \
		echo "Error: Please provide a message with MSG='description'"; \
		echo "Example: make migrate-create MSG='add user table'"; \
		exit 1; \
	fi
	alembic revision -m "$(MSG)"

# Show migration history
migrate-history:
	alembic history --verbose

# Show current migration
migrate-current:
	alembic current

# Start PostgreSQL with Docker
db-up:
	@echo "Starting PostgreSQL with Docker..."
	docker run -d \
		--name speech-db \
		-e POSTGRES_DB=speech_to_text \
		-e POSTGRES_USER=postgres \
		-e POSTGRES_PASSWORD=postgres \
		-p 5432:5432 \
		postgres:15
	@echo "Waiting for PostgreSQL to be ready..."
	@sleep 3
	@docker exec speech-db pg_isready -U postgres
	@echo "PostgreSQL is ready!"

# Stop PostgreSQL Docker container
db-down:
	@echo "Stopping PostgreSQL..."
	docker stop speech-db || true
	docker rm speech-db || true

# Reset database
db-reset: migrate-down migrate
	@echo "Database reset complete!"

# Run all tests
test:
	pytest tests/ -v

# Run unit tests only
test-unit:
	pytest tests/unit/ -v

# Run integration tests with test environment
test-integration:
	@echo "Starting test environment..."
	@docker-compose -f docker-compose.test.yml up -d
	@echo "Waiting for services..."
	@sleep 5
	@echo "Running integration tests..."
	@TEST_DATABASE_URL="postgresql://test_user:test_password@localhost:5433/test_transcription" \
	TEST_REDIS_URL="redis://localhost:6380/0" \
	pytest tests/integration/ -v || (docker-compose -f docker-compose.test.yml down && exit 1)
	@echo "Stopping test environment..."
	@docker-compose -f docker-compose.test.yml down
	@echo "Integration tests complete!"

# Run all tests with coverage
test-all:
	@echo "Starting test environment..."
	@docker-compose -f docker-compose.test.yml up -d
	@echo "Waiting for services..."
	@sleep 5
	@echo "Running all tests with coverage..."
	@TEST_DATABASE_URL="postgresql://test_user:test_password@localhost:5433/test_transcription" \
	TEST_REDIS_URL="redis://localhost:6380/0" \
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term || (docker-compose -f docker-compose.test.yml down && exit 1)
	@echo "Stopping test environment..."
	@docker-compose -f docker-compose.test.yml down
	@echo "All tests complete! Coverage report: htmlcov/index.html"

# Clean Python cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	@echo "Cleaned Python cache files"

# Test commands
test:
	@echo "Running all tests..."
	pytest

test-unit:
	@echo "Running unit tests..."
	pytest -m unit

test-integration:
	@echo "Running integration tests..."
	pytest -m integration

test-coverage:
	@echo "Running tests with coverage..."
	pytest --cov=app --cov-report=html --cov-report=term-missing
	@echo "Coverage report: htmlcov/index.html"

test-fast:
	@echo "Running tests in parallel..."
	pytest -n auto

test-docker:
	@echo "Running tests in Docker..."
	chmod +x scripts/run_tests.sh
	./scripts/run_tests.sh --docker

# Code quality commands
lint:
	@echo "Running linters..."
	ruff check app/ tests/

format:
	@echo "Formatting code..."
	black app/ tests/
	isort app/ tests/

pre-commit:
	@echo "Running pre-commit hooks..."
	pre-commit run --all-files

# Clean test artifacts
clean-test:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -f .coverage
	rm -f coverage.xml
	rm -f coverage.json
	@echo "Cleaned test artifacts"
	rm -rf htmlcov/ .coverage .pytest_cache/
	@echo "Cleaned Python cache files and test artifacts"
