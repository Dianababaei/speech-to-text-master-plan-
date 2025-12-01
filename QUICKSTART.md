# Quick Start Guide

Get up and running with the speech-to-text database in under 5 minutes.

## Prerequisites

- Python 3.8+ installed
- PostgreSQL 12+ running
- Git (to clone the repository)

## Step 1: Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt
```

## Step 2: Set Up Database

### Option A: Using Docker (Easiest)

```bash
# Start PostgreSQL with Docker
docker run -d \
  --name speech-db \
  -e POSTGRES_DB=speech_to_text \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  postgres:15
```

### Option B: Using Local PostgreSQL

```bash
# Create database (if not exists)
createdb speech_to_text

# Or using psql
psql -U postgres -c "CREATE DATABASE speech_to_text;"
```

## Step 3: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your database credentials
# vim .env  # or use your preferred editor
```

Example `.env` contents:
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=speech_to_text
DB_USER=postgres
DB_PASSWORD=postgres
```

## Step 4: Run Migrations

```bash
# Apply all migrations to create tables
alembic upgrade head
```

Expected output:
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 001, Initial schema with api_keys, lexicon_terms, jobs, and feedback tables
```

## Step 5: Verify Installation

```bash
# Check current database revision
alembic current

# Or connect to database and list tables
psql -h localhost -U postgres -d speech_to_text -c "\dt"
```

You should see four tables:
- `api_keys`
- `lexicon_terms`
- `jobs`
- `feedback`

## Verification Commands

```bash
# Show migration history
alembic history

# Show current revision
alembic current

# View table structure
psql -h localhost -U postgres -d speech_to_text -c "\d api_keys"
psql -h localhost -U postgres -d speech_to_text -c "\d lexicon_terms"
psql -h localhost -U postgres -d speech_to_text -c "\d jobs"
psql -h localhost -U postgres -d speech_to_text -c "\d feedback"
```

## Using Docker Compose (Complete Stack)

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: speech_to_text
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Then run:

```bash
# Start database
docker-compose up -d

# Run migrations
alembic upgrade head
```

## Troubleshooting

### "FATAL: password authentication failed"

Check your database credentials in `.env` file.

### "could not connect to server"

Ensure PostgreSQL is running:
```bash
# For Docker
docker ps | grep postgres

# For local PostgreSQL
pg_isready -h localhost
```

### "relation already exists"

Tables might already exist. Either:
```bash
# Drop and recreate
alembic downgrade base
alembic upgrade head

# Or mark as migrated
alembic stamp head
```

## Next Steps

- See `README.md` for detailed documentation
- Review migration file: `alembic/versions/001_initial_schema.py`
- Start building your application!

## Rollback (if needed)

```bash
# Rollback all migrations (removes all tables)
alembic downgrade base

# Rollback one step
alembic downgrade -1
```

## Clean Up

```bash
# Stop and remove Docker container
docker stop speech-db
docker rm speech-db

# Remove Docker volume (deletes all data)
docker volume rm speech_db_data
```

---

**Need help?** Check the full documentation in `README.md`
