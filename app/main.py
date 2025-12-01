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
