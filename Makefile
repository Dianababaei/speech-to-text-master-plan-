.PHONY: help install test test-unit test-integration test-coverage test-auth test-lexicon test-text test-numerals migrate migrate-down migrate-create migrate-history migrate-current db-up db-down db-reset clean

# Default target
help:
	@echo "Available commands:"
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
	@echo "Cleanup:"
	@echo "  make clean           - Remove Python cache files"

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

# Clean Python cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	@echo "Cleaned Python cache files"
