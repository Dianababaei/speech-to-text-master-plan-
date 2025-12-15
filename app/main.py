"""
Main FastAPI application entry point.

Configures the web server, routes, and background tasks for the
speech-to-text transcription service.
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.config.settings import get_settings
from app.services.storage import cleanup_old_audio_files, get_storage_stats

# Configure logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Background task for cleanup
async def cleanup_task():
    """Background task to periodically clean up old audio files."""
    from app.database import get_db
    
    logger.info("Starting cleanup background task")
    
    while True:
        try:
            # Wait for the configured interval
            await asyncio.sleep(settings.CLEANUP_INTERVAL_MINUTES * 60)
            
            logger.info("Running scheduled audio file cleanup")
            
            # Get database session
            db = next(get_db())
            try:
                stats = cleanup_old_audio_files(db)
                logger.info(
                    f"Cleanup completed: {stats['deleted']} files deleted, "
                    f"{stats['failed']} failed, {stats['scanned']} scanned"
                )
            finally:
                db.close()
                
        except asyncio.CancelledError:
            logger.info("Cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}", exc_info=True)
            # Continue running even if one iteration fails


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    
    Starts the cleanup background task on startup and cancels it on shutdown.
    """
    # Startup
    logger.info("Starting application")
    
    # Start the cleanup background task
    cleanup_task_handle = asyncio.create_task(cleanup_task())
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    cleanup_task_handle.cancel()
    try:
        await cleanup_task_handle
    except asyncio.CancelledError:
        pass


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="""
# Speech-to-Text Transcription Service

A comprehensive API for audio transcription with domain-specific lexicon support, 
post-processing, and feedback management.

## Features

- **Audio Transcription**: Submit audio files for asynchronous transcription using OpenAI Whisper
- **Lexicon Management**: Create and manage domain-specific lexicons (medical, legal, etc.)
- **Post-Processing**: Automatic text correction and normalization using custom lexicons
- **Feedback System**: Submit and review transcription corrections
- **Job Status**: Track transcription job progress and retrieve results

## Authentication

All endpoints require authentication via API key. Include your API key in the `X-API-Key` header.

## Rate Limiting

API requests may be rate-limited per API key to ensure fair usage.
Check response headers for rate limit information:
- `X-RateLimit-Limit`: Maximum requests allowed per time window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Unix timestamp when the rate limit resets

When rate limited, you'll receive a 429 status code with retry information.

## Common Workflows

1. **Transcribe Audio**: Submit audio file → Poll job status → Retrieve transcription
2. **Manage Lexicons**: Create lexicon → Add terms → Use in transcription
3. **Submit Feedback**: Get transcription → Submit correction → Admin reviews feedback
    """,
    version="1.0.0",
    lifespan=lifespan,
    contact={
        "name": "API Support",
        "email": "support@transcription-service.example.com",
    },
    license_info={
        "name": "Proprietary",
        "url": "https://transcription-service.example.com/license",
    },
    terms_of_service="https://transcription-service.example.com/terms",
    openapi_tags=[
        {
            "name": "transcription",
            "description": "Audio transcription submission and processing"
        },
        {
            "name": "jobs",
            "description": "Job status polling and result retrieval"
        },
        {
            "name": "lexicons",
            "description": "Lexicon and term management (CRUD operations)"
        },
        {
            "name": "Lexicons",
            "description": "Lexicon import/export operations"
        },
        {
            "name": "feedback",
            "description": "Feedback submission and review (admin-only)"
        },
        {
            "name": "health",
            "description": "Service health and monitoring endpoints"
        },
        {
            "name": "admin",
            "description": "Administrative operations"
        }
    ]
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from app.routers import lexicons, transcription
app.include_router(transcription.router)
app.include_router(lexicons.router)

try:
    from app.api import health
    app.include_router(health.router)
except ImportError:
    pass  # health module might not exist yet

try:
    from app.api.endpoints import feedback, jobs
    app.include_router(feedback.router)
    app.include_router(jobs.router)
except ImportError as e:
    logger.warning(f"Some endpoints not available: {e}")


@app.get(
    "/",
    tags=["health"],
    summary="Service information",
    description="Get basic service information and version",
    responses={
        200: {
            "description": "Service information",
            "content": {
                "application/json": {
                    "example": {
                        "service": "Speech-to-Text Transcription Service",
                        "version": "1.0.0",
                        "status": "running"
                    }
                }
            }
        }
    }
)
async def root():
    """
    Get service information.
    
    Returns basic metadata about the API including service name,
    version, and operational status.
    """
    return {
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running"
    }


@app.get(
    "/storage/stats",
    tags=["admin"],
    summary="Get storage statistics",
    description="""
Get storage usage statistics for audio files.

Returns information about:
- Total disk space and usage
- Audio file storage directory size
- Number of audio files stored

This endpoint can be used for monitoring storage capacity
and planning cleanup operations.
    """,
    responses={
        200: {
            "description": "Storage statistics",
            "content": {
                "application/json": {
                    "example": {
                        "total_space_gb": 100.0,
                        "used_space_gb": 45.2,
                        "free_space_gb": 54.8,
                        "audio_storage_gb": 2.3,
                        "file_count": 1245
                    }
                }
            }
        },
        500: {
            "description": "Failed to retrieve storage statistics",
            "content": {
                "application/json": {
                    "example": {"detail": "Failed to get storage statistics"}
                }
            }
        }
    }
)
async def storage_stats():
    """
    Get detailed storage usage statistics.
    
    Returns information about disk usage and audio file storage
    to help monitor capacity and plan cleanup operations.
    """
    try:
        stats = get_storage_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting storage stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get storage statistics")


@app.post(
    "/admin/cleanup",
    tags=["admin"],
    summary="Manually trigger cleanup",
    description="""
Manually trigger audio file cleanup process.

This endpoint allows administrators to manually trigger the cleanup
process that removes old audio files without waiting for the scheduled
background task.

**Cleanup Process:**
- Deletes audio files older than configured retention period
- Updates job records to mark files as deleted
- Returns statistics about deleted, failed, and scanned files

**Authentication:**
Requires valid API key (admin-level recommended)
    """,
    responses={
        200: {
            "description": "Cleanup completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "message": "Cleanup completed",
                        "stats": {
                            "deleted": 45,
                            "failed": 2,
                            "scanned": 150
                        }
                    }
                }
            }
        },
        500: {
            "description": "Cleanup operation failed",
            "content": {
                "application/json": {
                    "example": {"detail": "Cleanup failed: Database connection error"}
                }
            }
        }
    }
)
async def manual_cleanup():
    """
    Manually trigger audio file cleanup.
    
    Executes the cleanup process that removes old audio files
    based on the configured retention period.
    """
    from app.database import get_db
    
    try:
        logger.info("Manual cleanup triggered")
        db = next(get_db())
        try:
            stats = cleanup_old_audio_files(db)
            return {
                "status": "success",
                "message": "Cleanup completed",
                "stats": stats
            }
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error during manual cleanup: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


# Basic health endpoint (detailed health check is in /health from health router)
@app.get(
    "/healthz",
    tags=["health"],
    summary="Simple health check",
    description="Quick health check endpoint for basic liveness probe",
    responses={
        200: {
            "description": "Service is running",
            "content": {
                "application/json": {
                    "example": {"status": "healthy"}
                }
            }
        }
    }
)
async def health_check():
    """
    Simple health check for liveness probe.
    
    Returns immediate response without dependency checks.
    Use /health for comprehensive health status with dependency checks.
    """
    return {"status": "healthy"}


def custom_openapi():
    """
    Customize OpenAPI schema with security schemes and additional metadata.
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
        terms_of_service=app.terms_of_service,
        contact=app.contact,
        license_info=app.license_info,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for authentication. Contact support to obtain an API key."
        }
    }
    
    # Add security requirement globally (can be overridden per endpoint)
    # Note: Endpoints without authentication will override this
    openapi_schema["security"] = [{"ApiKeyAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
