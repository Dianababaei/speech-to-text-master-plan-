"""
FastAPI application entrypoint with lifecycle management.
Handles database and Redis connections with proper startup/shutdown.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy.orm import sessionmaker
from redis.asyncio import Redis, from_url as redis_from_url

from app.config import settings


# Configure structured logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events for database and Redis connections.
    """
    logger.info("Starting application initialization...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Max file size: {settings.MAX_FILE_SIZE} bytes")
    logger.info(f"Max workers: {settings.MAX_WORKERS}")
    
    # Startup: Initialize database connection pool
    try:
        logger.info("Initializing database connection pool...")
        # Convert postgresql:// to postgresql+asyncpg:// if needed
        db_url = settings.DATABASE_URL
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif not db_url.startswith("postgresql+asyncpg://"):
            db_url = f"postgresql+asyncpg://{db_url}"
        
        engine: AsyncEngine = create_async_engine(
            db_url,
            echo=settings.ENVIRONMENT == "dev",
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10
        )
        
        # Create async session factory
        async_session_maker = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Store in app state for access in routes
        app.state.db_engine = engine
        app.state.db_session_maker = async_session_maker
        logger.info("Database connection pool initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    # Startup: Initialize Redis connection
    try:
        logger.info("Initializing Redis connection...")
        redis_client: Redis = await redis_from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        
        # Test connection
        await redis_client.ping()
        
        # Store in app state for access in routes
        app.state.redis = redis_client
        logger.info("Redis connection initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")
        raise
    
    logger.info("Application startup complete")
    
    # Yield control to the application
    yield
    
    # Shutdown: Close connections gracefully
    logger.info("Starting application shutdown...")
    
    # Close Redis connection
    try:
        logger.info("Closing Redis connection...")
        await app.state.redis.aclose()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Error closing Redis connection: {e}")
    
    # Close database connections
    try:
        logger.info("Closing database connection pool...")
        await app.state.db_engine.dispose()
        logger.info("Database connection pool closed")
    except Exception as e:
        logger.error(f"Error closing database connection pool: {e}")
    
    logger.info("Application shutdown complete")


# Create FastAPI application instance
app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# Configure CORS middleware
cors_origins = settings.get_cors_origins()

# In production, use specific domains; in dev, allow localhost
if settings.ENVIRONMENT == "prod":
    # Filter out localhost origins in production for security
    cors_origins = [
        origin for origin in cors_origins 
        if not origin.startswith("http://localhost") and not origin.startswith("http://127.0.0.1")
    ]
    logger.info(f"CORS enabled for production origins: {cors_origins}")
else:
    logger.info(f"CORS enabled for development origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint to verify the application is running.
    Returns status of database and Redis connections.
    """
    try:
        # Check Redis connection
        await app.state.redis.ping()
        redis_status = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        redis_status = "unhealthy"
    
    try:
        # Check database connection
        async with app.state.db_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    return {
        "status": "ok" if redis_status == "healthy" and db_status == "healthy" else "degraded",
        "environment": settings.ENVIRONMENT,
        "version": settings.APP_VERSION,
        "services": {
            "database": db_status,
            "redis": redis_status
        }
    }


@app.get("/", tags=["System"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Speech-to-Text API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health"
    }


# Export app and settings for external use
__all__ = ["app", "settings"]
