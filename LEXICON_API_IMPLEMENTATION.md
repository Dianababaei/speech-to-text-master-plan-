# Lexicon CRUD API Implementation

## Overview

This document describes the implementation of REST API endpoints for managing lexicon terms within specific lexicons. The system supports swappable domain-specific lexicons (radiology, cardiology, general, etc.) for improving transcription accuracy.

## Implemented Components

### 1. Database Migration
**File:** `alembic/versions/002_add_lexicon_id_replacement.py`

- Adds `lexicon_id` field to identify which lexicon a term belongs to
- Adds `replacement` field to store the corrected term
- Updates unique constraint to `(lexicon_id, normalized_term)` allowing same term in different lexicons
- Creates index on `lexicon_id` for query performance

### 2. Database Model
**File:** `app/models/lexicon.py`

- `LexiconTerm` SQLAlchemy model mapping to `lexicon_terms` table
- Key fields:
  - `id`: Primary key
  - `lexicon_id`: Lexicon identifier (e.g., "radiology", "cardiology")
  - `term`: The term to match in transcriptions
  - `normalized_term`: Lowercase version for case-insensitive matching
  - `replacement`: The corrected term
  - `is_active`: For soft delete functionality
  - `created_at`, `updated_at`: Timestamps

### 3. Pydantic Schemas
**File:** `app/schemas/lexicon.py`

- `TermCreate`: Request schema for creating terms
- `TermUpdate`: Request schema for updating terms
- `TermResponse`: Response schema for single term
- `TermListResponse`: Response schema for paginated term lists

All schemas include validation and OpenAPI examples.

### 4. Service Layer
**File:** `app/services/lexicon_service.py`

Business logic functions:
- `create_term()`: Creates new term with uniqueness validation
- `get_terms()`: Returns paginated list of active terms
- `get_term_by_id()`: Retrieves specific term
- `update_term()`: Updates existing term with validation
- `soft_delete_term()`: Marks term as inactive
- `check_term_uniqueness()`: Case-insensitive uniqueness check

### 5. API Router
**File:** `app/routers/lexicons.py`

Implements 5 REST endpoints:

#### POST /lexicons/{lexicon_id}/terms
- Creates new term in specified lexicon
- Validates term uniqueness (case-insensitive)
- Returns 201 Created with term object
- Returns 409 Conflict if term already exists

#### GET /lexicons/{lexicon_id}/terms
- Lists all active terms in lexicon
- Supports pagination via `?page=1&limit=50`
- Returns list with total count

#### GET /lexicons/{lexicon_id}/terms/{term_id}
- Returns specific term details
- Returns 404 Not Found if term doesn't exist

#### PUT /lexicons/{lexicon_id}/terms/{term_id}
- Updates existing term
- Validates uniqueness of new term value
- Returns 404 if term not found
- Returns 409 if update would create duplicate

#### DELETE /lexicons/{lexicon_id}/terms/{term_id}
- Soft deletes term (sets `is_active=false`)
- Maintains audit trail
- Returns 204 No Content on success
- Returns 404 if term not found

### 6. Main Application
**File:** `app/main.py`

- Registered lexicons router with the FastAPI application

## Features

### Authentication
- All endpoints require valid API key via `X-API-Key` header
- Uses existing authentication middleware from task #23

### Validation
- Lexicon ID: Alphanumeric with hyphens/underscores, max 100 characters
- Term and replacement: Non-empty strings, max 255 characters
- Term uniqueness: Case-insensitive within each lexicon
- Term ID: Positive integer

### Error Handling
- **400**: Bad request (validation errors)
- **401**: Unauthorized (missing/invalid API key)
- **404**: Not Found (term or lexicon doesn't exist)
- **409**: Conflict (duplicate term)
- **422**: Unprocessable Entity (invalid format)
- **500**: Internal Server Error (unexpected errors)

### Soft Delete
- Terms are never physically deleted
- `is_active=false` maintains historical data
- Inactive terms excluded from list queries
- Supports audit trail and versioning

### Pagination
- Default: page=1, limit=50
- Max limit: 100 items per page
- Returns total count for client-side pagination

### Timestamps
- `created_at`: Set automatically on creation
- `updated_at`: Updated automatically on modification
- Timezone-aware timestamps using PostgreSQL `CURRENT_TIMESTAMP`

## Usage Examples

### Create a Term
```bash
curl -X POST "http://localhost:8000/lexicons/radiology/terms" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "term": "atreal fibrillation",
    "replacement": "atrial fibrillation"
  }'
```

### List Terms
```bash
curl -X GET "http://localhost:8000/lexicons/radiology/terms?page=1&limit=50" \
  -H "X-API-Key: your-api-key"
```

### Get Specific Term
```bash
curl -X GET "http://localhost:8000/lexicons/radiology/terms/1" \
  -H "X-API-Key: your-api-key"
```

### Update Term
```bash
curl -X PUT "http://localhost:8000/lexicons/radiology/terms/1" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "term": "atrial fibrillation",
    "replacement": "atrial fibrillation"
  }'
```

### Delete Term
```bash
curl -X DELETE "http://localhost:8000/lexicons/radiology/terms/1" \
  -H "X-API-Key: your-api-key"
```

## OpenAPI Documentation

All endpoints are fully documented in the OpenAPI specification available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Database Setup

Before using the API, run the migration:

```bash
alembic upgrade head
```

This will apply the schema changes to add `lexicon_id` and `replacement` fields to the `lexicon_terms` table.

## Dependencies

- Task #16: lexicon_terms table schema (✓ completed, enhanced)
- Task #22: API key generation and storage (✓ used)
- Task #23: API key validation middleware (✓ used)

## Files Created/Modified

### Created:
- `alembic/versions/002_add_lexicon_id_replacement.py`
- `app/models/lexicon.py`
- `app/schemas/lexicon.py`
- `app/services/lexicon_service.py`
- `app/routers/lexicons.py`

### Modified:
- `app/models/__init__.py` (added LexiconTerm export)
- `app/main.py` (registered lexicons router)

## Success Criteria

✅ Can create new terms via POST with proper validation  
✅ Can list all active terms with pagination working correctly  
✅ Can retrieve individual term details  
✅ Can update existing terms with validation  
✅ Soft delete sets is_active=false without removing data  
✅ Duplicate terms are rejected with 409 error  
✅ All endpoints require authentication  
✅ Proper error responses for invalid inputs  
✅ OpenAPI spec accurately documents all endpoints
