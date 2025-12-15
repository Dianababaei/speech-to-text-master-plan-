# OpenAPI Specification Documentation

This document describes the comprehensive OpenAPI 3.0 specification implemented for the Speech-to-Text Transcription Service API.

## Overview

The API now includes complete OpenAPI documentation that enables:
- **Independent QA Testing**: QA team can use the spec to generate test cases
- **Client SDK Generation**: Automatically generate SDKs in multiple languages
- **Interactive Documentation**: Swagger UI and ReDoc interfaces
- **API Discovery**: Complete endpoint documentation with examples

## Accessing Documentation

### Interactive Documentation Interfaces

1. **Swagger UI** (Interactive API Explorer)
   - URL: `http://localhost:8000/docs`
   - Features: Try out API calls, view request/response examples
   - Best for: Interactive testing and exploration

2. **ReDoc** (Clean Documentation)
   - URL: `http://localhost:8000/redoc`
   - Features: Beautiful, responsive documentation
   - Best for: Reading and understanding the API

3. **OpenAPI JSON Specification**
   - URL: `http://localhost:8000/openapi.json`
   - Features: Complete machine-readable API specification
   - Best for: SDK generation, automated testing, integration tools

## Documentation Features

### 1. API Metadata

Complete API information including:
- **Title**: Speech-to-Text Transcription Service
- **Version**: 1.0.0
- **Description**: Comprehensive markdown documentation
- **Contact Information**: Support email
- **License**: Proprietary license information
- **Terms of Service**: Link to terms

### 2. Authentication Documentation

API key authentication is fully documented:

```yaml
securitySchemes:
  ApiKeyAuth:
    type: apiKey
    in: header
    name: X-API-Key
    description: API key for authentication. Contact support to obtain an API key.
```

All protected endpoints automatically include authentication requirements in their documentation.

**Usage Example:**
```bash
curl -X GET "http://localhost:8000/jobs/{job_id}" \
  -H "X-API-Key: your_api_key_here"
```

### 3. Endpoint Categories (Tags)

Endpoints are organized into logical groups:

- **transcription**: Audio transcription submission
- **jobs**: Job status polling and results
- **lexicons**: Lexicon and term management
- **feedback**: Feedback submission and review
- **health**: Service health monitoring
- **admin**: Administrative operations

### 4. Request/Response Documentation

Every endpoint includes:

#### Request Documentation
- Path parameters with descriptions and examples
- Query parameters with validation rules
- Request body schemas with field descriptions
- Header requirements (API keys, content types)

#### Response Documentation
- Success responses (200, 201, 202) with examples
- Client error responses (400, 401, 403, 404, 409, 413, 422, 429)
- Server error responses (500, 503)
- Each response includes:
  - Status code
  - Description
  - Response schema
  - Example payload

### 5. Pydantic Models with Rich Metadata

All request/response models include:
- Field descriptions
- Data types and validation rules
- Example values
- Default values
- Constraints (min/max length, patterns, enums)

Example:
```python
class TranscriptionSubmitResponse(BaseModel):
    job_id: str = Field(
        ...,
        description="Unique job identifier (UUID) for tracking transcription status",
        examples=["123e4567-e89b-12d3-a456-426614174000"]
    )
    status: str = Field(
        ...,
        description="Initial job status (always 'pending' on submission)",
        examples=["pending"]
    )
```

### 6. Error Response Models

Standardized error responses across all endpoints:

```python
# 400 Bad Request
{
  "detail": "Invalid file format. Allowed formats: WAV, MP3, M4A"
}

# 401 Unauthorized
{
  "detail": "API key is required. Provide X-API-Key header."
}

# 429 Rate Limited
{
  "detail": "Rate limit exceeded. Please retry after 60 seconds.",
  "retry_after": 60,
  "limit": 100,
  "remaining": 0,
  "reset": 1705320000
}
```

## API Endpoints

### Transcription Endpoints

#### POST /transcribe
Submit audio file for transcription
- **Authentication**: Required (API Key)
- **Request**: Multipart form with audio file
- **Response**: 202 Accepted with job_id
- **Errors**: 400 (invalid format), 401 (auth), 413 (file too large), 500

### Job Endpoints

#### GET /jobs/{job_id}
Poll job status and retrieve results
- **Authentication**: Required (API Key)
- **Response**: Job status, timestamps, transcription results
- **Errors**: 400 (invalid UUID), 401 (auth), 404 (not found), 500

### Feedback Endpoints

#### POST /jobs/{job_id}/feedback
Submit correction feedback
- **Authentication**: Required (API Key)
- **Request**: Original and corrected text
- **Response**: 201 Created with feedback_id
- **Errors**: 400 (validation), 401 (auth), 404 (job not found), 422

#### GET /feedback
List feedback records (Admin only)
- **Authentication**: Required (Admin API Key)
- **Query Parameters**: status, lexicon_id, date filters, pagination
- **Response**: Paginated feedback list
- **Errors**: 400 (invalid params), 401/403 (auth), 500

### Health Endpoints

#### GET /health
Comprehensive health check with dependency status
- **Authentication**: None
- **Response**: 200 (healthy) or 503 (unhealthy)
- **Checks**: PostgreSQL, Redis

#### GET /healthz
Simple liveness check
- **Authentication**: None
- **Response**: 200 with basic status

### Admin Endpoints

#### GET /storage/stats
Storage usage statistics
- **Authentication**: Recommended (API Key)
- **Response**: Disk usage and file counts

#### POST /admin/cleanup
Trigger manual cleanup of old audio files
- **Authentication**: Recommended (Admin API Key)
- **Response**: Cleanup statistics

## Common Workflows

### 1. Audio Transcription Workflow

```bash
# Step 1: Submit audio file
curl -X POST "http://localhost:8000/transcribe?lexicon=radiology" \
  -H "X-API-Key: your_key" \
  -F "audio=@recording.wav"

# Response:
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "pending",
  "created_at": "2024-01-15T10:30:00Z",
  "lexicon_id": "radiology"
}

# Step 2: Poll job status
curl -X GET "http://localhost:8000/jobs/123e4567-e89b-12d3-a456-426614174000" \
  -H "X-API-Key: your_key"

# Response (when complete):
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "created_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:31:30Z",
  "original_text": "The patient has mild edema",
  "processed_text": "The patient has mild edema.",
  "error_message": null
}
```

### 2. Feedback Submission Workflow

```bash
# Submit correction
curl -X POST "http://localhost:8000/jobs/123e4567-e89b-12d3-a456-426614174000/feedback" \
  -H "X-API-Key: your_key" \
  -H "Content-Type: application/json" \
  -d '{
    "original_text": "The patient has diabetis",
    "corrected_text": "The patient has diabetes",
    "created_by": "dr.smith@hospital.com"
  }'

# Admin reviews feedback
curl -X GET "http://localhost:8000/feedback?status=pending" \
  -H "X-API-Key: admin_key"
```

## Rate Limiting

Rate limiting information is documented but implementation-dependent:

**Response Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705320000
```

**Rate Limited Response (429):**
```json
{
  "detail": "Rate limit exceeded. Please retry after 60 seconds.",
  "retry_after": 60,
  "limit": 100,
  "remaining": 0,
  "reset": 1705320000
}
```

## SDK Generation

The OpenAPI spec can be used to generate client SDKs:

### Using OpenAPI Generator

```bash
# Download the spec
curl http://localhost:8000/openapi.json > openapi.json

# Generate Python client
openapi-generator-cli generate \
  -i openapi.json \
  -g python \
  -o ./client-python

# Generate TypeScript client
openapi-generator-cli generate \
  -i openapi.json \
  -g typescript-axios \
  -o ./client-typescript

# Generate Java client
openapi-generator-cli generate \
  -i openapi.json \
  -g java \
  -o ./client-java
```

### Supported Languages
- Python
- JavaScript/TypeScript
- Java
- Go
- Ruby
- PHP
- C#
- And 50+ more languages

## Testing with OpenAPI Spec

### Using Postman

1. Import the OpenAPI spec:
   - Open Postman
   - Click "Import"
   - Enter URL: `http://localhost:8000/openapi.json`
   - Postman creates a complete collection with all endpoints

### Using Swagger Codegen

```bash
# Generate test code
swagger-codegen generate \
  -i http://localhost:8000/openapi.json \
  -l python \
  -o ./test-client
```

### Using OpenAPI Validator

```bash
# Validate the spec
openapi-spec-validator http://localhost:8000/openapi.json
```

## Validation and Quality

The OpenAPI specification includes:

✅ **Complete endpoint documentation** for all routes
✅ **Request/response examples** for common use cases
✅ **Authentication scheme** documentation
✅ **Error response models** for all status codes
✅ **Field-level validation** rules and constraints
✅ **Enum documentation** for status values
✅ **Pagination parameters** with limits
✅ **File upload** specifications
✅ **Health check** endpoints

## Best Practices Implemented

1. **Consistent Error Format**: All errors use standardized response models
2. **Rich Descriptions**: Every endpoint, parameter, and field is documented
3. **Examples Everywhere**: Request/response examples for all scenarios
4. **Security Documentation**: Clear authentication requirements
5. **Status Code Coverage**: All possible responses documented
6. **Type Safety**: Strong typing with Pydantic models
7. **Validation Rules**: Min/max lengths, patterns, enums
8. **Deprecation Strategy**: Fields marked for deprecation (if any)

## Maintenance

To keep the OpenAPI spec up-to-date:

1. **Add docstrings** to new endpoints using FastAPI decorators
2. **Update Pydantic models** with Field descriptions
3. **Include examples** in request/response schemas
4. **Document error cases** with appropriate status codes
5. **Test documentation** by viewing Swagger UI at `/docs`

## Support

For questions about the API or OpenAPI specification:
- Email: support@transcription-service.example.com
- Documentation: http://localhost:8000/docs
- OpenAPI Spec: http://localhost:8000/openapi.json
