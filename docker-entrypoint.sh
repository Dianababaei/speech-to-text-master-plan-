#!/bin/bash
# Docker entrypoint script for auto-running Alembic migrations
# This script runs database migrations before starting the FastAPI application

set -e

echo "========================================="
echo "Starting Docker Entrypoint Script"
echo "========================================="

# Display environment info (without sensitive data)
echo "Database Host: ${DB_HOST:-not set}"
echo "Database Port: ${DB_PORT:-not set}"
echo "Database Name: ${DB_NAME:-not set}"
echo "Database User: ${DB_USER:-not set}"

# Wait for PostgreSQL to be ready
echo ""
echo "Waiting for PostgreSQL to be ready..."
max_retries=30
retry_count=0

until pg_isready -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "${DB_USER:-postgres}" || [ $retry_count -eq $max_retries ]; do
    retry_count=$((retry_count + 1))
    echo "PostgreSQL is unavailable - sleeping (attempt $retry_count/$max_retries)"
    sleep 2
done

if [ $retry_count -eq $max_retries ]; then
    echo "ERROR: PostgreSQL did not become ready in time"
    exit 1
fi

echo "PostgreSQL is ready!"

# Run Alembic migrations
echo ""
echo "Running Alembic migrations..."
echo "========================================="

# Check if AUTO_MIGRATE is enabled (default: true)
AUTO_MIGRATE=${AUTO_MIGRATE:-true}

if [ "$AUTO_MIGRATE" = "true" ]; then
    echo "AUTO_MIGRATE is enabled"
    
    # Show current database revision
    echo "Current database revision:"
    alembic current || echo "No migrations applied yet"
    
    # Run migrations
    echo ""
    echo "Applying migrations to head..."
    alembic upgrade head
    
    # Show new database revision
    echo ""
    echo "New database revision:"
    alembic current
    
    echo "========================================="
    echo "Migrations completed successfully!"
else
    echo "AUTO_MIGRATE is disabled - skipping migrations"
    echo "Run migrations manually with: alembic upgrade head"
fi

echo "========================================="

# Execute the main command (typically starting FastAPI)
echo ""
echo "Starting application: $@"
echo "========================================="

exec "$@"
