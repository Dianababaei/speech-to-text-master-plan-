from fastapi import FastAPI
import redis
from app.config.settings import settings
from app.database import engine
from app.api import health

# Create FastAPI application
app = FastAPI(
    title="Speech-to-Text API",
    description="Speech-to-text prototype with OpenAI API",
    version="1.0.0"
)

# Initialize Redis connection pool
redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=settings.HEALTH_CHECK_TIMEOUT,
    socket_timeout=settings.HEALTH_CHECK_TIMEOUT
)

# Register routers
app.include_router(health.router)


@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    print("Application starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    print("Application shutting down...")
    redis_client.close()


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Speech-to-Text API", "status": "running"}
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
    description="Speech-to-text transcription service with multi-language support",
    version="1.0.0",
    lifespan=lifespan
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
from app.routers import lexicons
app.include_router(lexicons.router)


@app.get("/")
async def root():
    """Root endpoint returning service information."""
    return {
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/storage/stats")
async def storage_stats():
    """
    Get storage statistics.
    
    Returns information about disk usage and audio file storage.
    """
    try:
        stats = get_storage_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting storage stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get storage statistics")


@app.post("/admin/cleanup")
async def manual_cleanup():
    """
    Manually trigger audio file cleanup.
    
    This endpoint allows administrators to manually trigger the cleanup
    process without waiting for the scheduled background task.
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


# Health check endpoint (for the upcoming task)
@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
