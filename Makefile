.PHONY: help install migrate migrate-down migrate-create migrate-history migrate-current db-up db-down db-reset clean test test-unit test-integration test-all

# Default target
help:
	@echo "Available commands:"
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

# Install dependencies
install:
	pip install -r requirements.txt

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
	rm -rf htmlcov/ .coverage .pytest_cache/
	@echo "Cleaned Python cache files and test artifacts"
