# Speech-to-Text Prototype

A speech-to-text prototype built with the OpenAI API (gpt-4o-transcribe / whisper-1) that supports multi-language transcription with custom lexicon support.

## Project Overview

This project transcribes multi-language audio while keeping each word in its original language or script (code-switching). It includes feedback mechanisms for continuous learning and improvement.

## Database Setup

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Alembic (installed via `pip install alembic`)
- psycopg2 or psycopg2-binary (PostgreSQL driver)

### Environment Variables

Set the following environment variables for database connection:

```bash
# Database Configuration
export DB_HOST=localhost          # PostgreSQL host
export DB_PORT=5432               # PostgreSQL port
export DB_NAME=speech_to_text     # Database name
export DB_USER=postgres           # Database user
export DB_PASSWORD=your_password  # Database password

# Alternative: Use DATABASE_URL (takes precedence)
export DATABASE_URL=postgresql://user:password@localhost:5432/speech_to_text
```

### Database Schema

The application uses four core tables:

1. **api_keys** - API authentication keys
2. **lexicon_terms** - Domain-specific terms for transcription improvement
3. **jobs** - Transcription jobs and their status
4. **feedback** - Reviewer corrections and learning data

## Migration Management

This project uses [Alembic](https://alembic.sqlalchemy.org/) for database schema migrations.

### Initial Setup

1. **Install dependencies**:
   ```bash
   pip install alembic psycopg2-binary
   ```

2. **Configure environment variables** (see above)

3. **Run initial migration**:
   ```bash
   alembic upgrade head
   ```

### Manual Migration Commands

#### Apply all migrations
```bash
alembic upgrade head
```

#### Rollback all migrations
```bash
alembic downgrade base
```

#### Rollback one migration
```bash
alembic downgrade -1
```

#### Show current revision
```bash
alembic current
```

#### Show migration history
```bash
alembic history --verbose
```

#### Create a new migration (after model changes)
```bash
alembic revision -m "description of changes"
```

#### Auto-generate migration from model changes
```bash
# Note: Requires SQLAlchemy models to be imported in alembic/env.py
alembic revision --autogenerate -m "description of changes"
```

### Docker Integration

#### Approach 1: Auto-Run Migrations on Startup (Recommended)

Use the provided `docker-entrypoint.sh` script to automatically run migrations when the container starts.

**Dockerfile example**:
```dockerfile
FROM python:3.11-slim

# Install PostgreSQL client for pg_isready
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy application files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make entrypoint script executable
RUN chmod +x docker-entrypoint.sh

# Set entrypoint
ENTRYPOINT ["./docker-entrypoint.sh"]

# Default command (start FastAPI)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml example**:
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

  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DB_HOST: db
      DB_PORT: 5432
      DB_NAME: speech_to_text
      DB_USER: postgres
      DB_PASSWORD: postgres
      AUTO_MIGRATE: "true"  # Enable automatic migrations
    depends_on:
      - db

volumes:
  postgres_data:
```

**To disable auto-migration**:
```yaml
environment:
  AUTO_MIGRATE: "false"
```

#### Approach 2: Manual Migration Execution

Run migrations manually before starting the application:

**Using docker-compose**:
```bash
# Start only the database
docker-compose up -d db

# Run migrations
docker-compose run --rm app alembic upgrade head

# Start the application
docker-compose up -d app
```

**Using docker run**:
```bash
# Start database
docker run -d --name db -e POSTGRES_PASSWORD=postgres postgres:15

# Run migrations
docker run --rm --network container:db \
  -e DB_HOST=localhost \
  -e DB_PASSWORD=postgres \
  your-app-image alembic upgrade head

# Start application
docker run -d --name app --network container:db \
  -e DB_HOST=localhost \
  -e DB_PASSWORD=postgres \
  -p 8000:8000 \
  your-app-image
```

### Development Workflow

#### 1. Local Development

```bash
# Set up local environment
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=speech_to_text_dev
export DB_USER=postgres
export DB_PASSWORD=postgres

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

#### 2. Testing Migrations

```bash
# Test upgrade
alembic upgrade head

# Verify tables were created
psql -h localhost -U postgres -d speech_to_text -c "\dt"

# Test downgrade
alembic downgrade base

# Verify tables were dropped
psql -h localhost -U postgres -d speech_to_text -c "\dt"

# Re-apply migrations
alembic upgrade head
```

#### 3. Production Deployment

**Option A: Auto-migration (simpler, good for small teams)**
- Set `AUTO_MIGRATE=true` in production environment
- Migrations run automatically on container startup
- Requires database backup strategy

**Option B: Manual migration (safer, recommended for production)**
- Set `AUTO_MIGRATE=false` in production environment
- Run migrations manually during deployment:
  ```bash
  # SSH to production server or use CI/CD pipeline
  alembic upgrade head
  ```
- Allows for verification before starting application
- Better control over rollback procedures

### Migration Best Practices

1. **Always backup the database** before running migrations in production
2. **Test migrations** on a staging environment first
3. **Review migration scripts** before applying them
4. **Use transactions** - Alembic uses transactions by default, but verify
5. **Monitor migration execution** - especially for large tables
6. **Plan for rollback** - ensure downgrade scripts are tested
7. **Version control** - commit migration scripts to git
8. **Document schema changes** - add comments to migration scripts

### Troubleshooting

#### Migration fails with "relation already exists"

The table might already exist. Options:
```bash
# Option 1: Stamp the database with current revision (if tables are correct)
alembic stamp head

# Option 2: Drop all tables and re-run migrations
alembic downgrade base
alembic upgrade head
```

#### Cannot connect to database

Check environment variables and network connectivity:
```bash
# Test PostgreSQL connection
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME

# Or using pg_isready
pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER
```

#### Migration hangs or times out

- Check for locks: `SELECT * FROM pg_locks WHERE granted = false;`
- Ensure no other processes are using the database
- Increase timeout in alembic.ini if needed

#### Rollback failed

If downgrade fails, you may need to manually fix the database:
```bash
# Show current state
alembic current

# Show SQL without executing
alembic downgrade -1 --sql

# Manually execute SQL or fix issues, then stamp
alembic stamp <revision>
```

### Schema Overview

#### api_keys Table
- Stores API authentication keys (SHA256 hashed)
- Includes rate limiting and expiration support
- Tracks last usage for monitoring

#### lexicon_terms Table
- Domain-specific terms (drug names, brand names, etc.)
- Normalized terms for matching
- Frequency tracking for learning
- Supports alternatives and metadata

#### jobs Table
- Transcription job tracking
- Audio file metadata
- Processing status and timing
- References api_keys for authentication

#### feedback Table
- Reviewer corrections and edits
- Diff data for analysis
- Accuracy scoring
- Extracts new terms for lexicon
- References jobs table (CASCADE delete)

### Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## Contributing

When making schema changes:
1. Update SQLAlchemy models (if applicable)
2. Create a new migration: `alembic revision -m "description"`
3. Update the migration script with upgrade/downgrade logic
4. Test both upgrade and downgrade
5. Document changes in migration comments
6. Commit migration script to version control

## License

[Your License Here]
