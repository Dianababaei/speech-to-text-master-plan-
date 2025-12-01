# Job Status API Endpoint

## Overview
This module implements the job status retrieval endpoint (`GET /jobs/{job_id}`) that allows clients to poll for transcription progress and results.

## Integration

### 1. Register the Router
Add the jobs router to your main FastAPI application:

```python
from fastapi import FastAPI
from app.api.endpoints.jobs import router as jobs_router

app = FastAPI()
app.include_router(jobs_router)
```

### 2. Register Exception Handler
To ensure invalid UUID formats return 400 instead of 422, register the custom exception handler:

```python
from fastapi.exceptions import RequestValidationError
from app.api.exceptions import validation_exception_handler

app.add_exception_handler(RequestValidationError, validation_exception_handler)
```

### 3. Required Dependencies
The following dependencies must be implemented (as mentioned in the task requirements):

#### Database Session (`app.db.session`)
```python
# app/db/session.py
from sqlalchemy.orm import Session

def get_db() -> Session:
    """Yield database session."""
    # Your database session implementation
    pass
```

#### Job Model (`app.models.jobs`)
```python
# app/models/jobs.py
from sqlalchemy import Column, String, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid

class Job:
    """Job database model."""
    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_key_id = Column(Integer, nullable=False)
    status = Column(String, nullable=False)  # pending|processing|completed|failed
    created_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    original_text = Column(String, nullable=True)
    processed_text = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
```

#### API Key Authentication (`app.api.dependencies`)
```python
# app/api/dependencies.py
from fastapi import Header, HTTPException, status

def get_api_key_id(x_api_key: str = Header(..., alias="X-API-Key")) -> int:
    """
    Validate API key and return associated api_key_id.
    
    Raises:
        HTTPException: 401 if API key is invalid or missing
    """
    # Your API key validation logic
    # Return the api_key_id associated with the valid API key
    pass
```

## Endpoint Specification

### Request
- **Method**: GET
- **Path**: `/jobs/{job_id}`
- **Headers**: 
  - `X-API-Key`: Valid API key (required)
- **Path Parameters**:
  - `job_id`: UUID format

### Response
- **Status Code**: 200 OK
- **Body**:
```json
{
  "job_id": "uuid",
  "status": "pending|processing|completed|failed",
  "created_at": "ISO 8601 timestamp",
  "completed_at": "ISO 8601 timestamp or null",
  "original_text": "string or null",
  "processed_text": "string or null",
  "error_message": "string or null"
}
```

### Error Responses
- **400 Bad Request**: Invalid UUID format
- **401 Unauthorized**: Missing or invalid API key
- **404 Not Found**: Job doesn't exist or belongs to different API key

## Business Rules
1. Clients can only access jobs created with their API key
2. `original_text` and `processed_text` are null for pending/processing jobs
3. `error_message` is populated only for failed jobs
4. `completed_at` is null until job completes (successfully or with failure)

## Testing
Example curl request:
```bash
curl -X GET "http://localhost:8000/jobs/123e4567-e89b-12d3-a456-426614174000" \
  -H "X-API-Key: your-api-key-here"
```

## OpenAPI Documentation
Once the endpoint is registered, interactive API documentation will be available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
