from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Response, status
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, TimeoutError as SQLTimeoutError
from pydantic import BaseModel, Field
import redis
from app.database import engine
from app.config.settings import settings
from app.schemas.errors import ERROR_RESPONSES
import asyncio
from concurrent.futures import TimeoutError
import signal

router = APIRouter(tags=["health"])


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(
        ...,
        description="Overall health status: 'healthy' or 'unhealthy'",
        examples=["healthy", "unhealthy"]
    )
    postgres: str = Field(
        ...,
        description="PostgreSQL database status: 'ok' or 'error'",
        examples=["ok", "error"]
    )
    redis: str = Field(
        ...,
        description="Redis cache status: 'ok' or 'error'",
        examples=["ok", "error"]
    )
    timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp of the health check",
        examples=["2024-01-15T10:30:00Z"]
    )
    postgres_error: str = Field(
        None,
        description="Error message if PostgreSQL check failed"
    )
    redis_error: str = Field(
        None,
        description="Error message if Redis check failed"
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "status": "healthy",
                    "postgres": "ok",
                    "redis": "ok",
                    "timestamp": "2024-01-15T10:30:00Z"
                },
                {
                    "status": "unhealthy",
                    "postgres": "error",
                    "redis": "ok",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "postgres_error": "Database connection failed: connection timeout"
                }
            ]
        }


def check_postgres() -> tuple[str, str]:
    """
    Check PostgreSQL database connectivity.
    
    Returns:
        Tuple of (status, error_message)
        status: "ok" if healthy, "error" if unhealthy
        error_message: Error details if unhealthy, empty string if healthy
    """
    try:
        # Create a connection with timeout
        with engine.connect() as connection:
            # Execute simple query to verify connectivity
            result = connection.execute(text("SELECT 1"))
            result.fetchone()
        return "ok", ""
    except (OperationalError, SQLTimeoutError) as e:
        return "error", f"Database connection failed: {str(e)}"
    except Exception as e:
        return "error", f"Unexpected database error: {str(e)}"


def check_redis() -> tuple[str, str]:
    """
    Check Redis connectivity.
    
    Returns:
        Tuple of (status, error_message)
        status: "ok" if healthy, "error" if unhealthy
        error_message: Error details if unhealthy, empty string if healthy
    """
    try:
        # Create Redis client for health check
        redis_client = redis.from_url(settings.REDIS_URL, socket_timeout=5)
        
        # Simple ping command to verify connectivity
        response = redis_client.ping()
        if response:
            return "ok", ""
        else:
            return "error", "Redis ping returned False"
    except redis.ConnectionError as e:
        return "error", f"Redis connection failed: {str(e)}"
    except redis.TimeoutError as e:
        return "error", f"Redis timeout: {str(e)}"
    except Exception as e:
        return "error", f"Unexpected Redis error: {str(e)}"


def run_with_timeout(func, timeout_seconds: int):
    """
    Run a function with a timeout.
    
    Args:
        func: Function to execute
        timeout_seconds: Timeout in seconds
        
    Returns:
        Result from the function
        
    Raises:
        TimeoutError: If function execution exceeds timeout
    """
    import concurrent.futures
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(func)
        try:
            return future.result(timeout=timeout_seconds)
        except concurrent.futures.TimeoutError:
            return "error", f"Health check timed out after {timeout_seconds} seconds"


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Service health check",
    description="""
Check the health status of the service and its dependencies.

This endpoint verifies connectivity to:
- **PostgreSQL Database**: Primary data store for jobs, lexicons, and feedback
- **Redis Cache**: Caching layer for lexicon data

## Health Status

- **200 OK**: All dependencies are operational
- **503 Service Unavailable**: One or more dependencies are unhealthy

Each dependency is checked with a configurable timeout (default 5 seconds).

## Response Fields

- `status`: Overall service health ('healthy' or 'unhealthy')
- `postgres`: PostgreSQL database status ('ok' or 'error')
- `redis`: Redis cache status ('ok' or 'error')
- `timestamp`: ISO 8601 timestamp of the check
- `postgres_error`: Error details if PostgreSQL is unhealthy (optional)
- `redis_error`: Error details if Redis is unhealthy (optional)

## Use Cases

- **Load Balancer**: Use for health checks and traffic routing
- **Monitoring**: Set up alerts when health status becomes unhealthy
- **Deployment**: Verify service is ready before accepting traffic
    """,
    responses={
        200: {
            "description": "Service is healthy - all dependencies operational",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "postgres": "ok",
                        "redis": "ok",
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                }
            }
        },
        503: {
            "description": "Service is unhealthy - one or more dependencies down",
            "content": {
                "application/json": {
                    "examples": {
                        "database_error": {
                            "summary": "Database connection failed",
                            "value": {
                                "status": "unhealthy",
                                "postgres": "error",
                                "redis": "ok",
                                "timestamp": "2024-01-15T10:30:00Z",
                                "postgres_error": "Database connection failed: connection timeout"
                            }
                        },
                        "redis_error": {
                            "summary": "Redis connection failed",
                            "value": {
                                "status": "unhealthy",
                                "postgres": "ok",
                                "redis": "error",
                                "timestamp": "2024-01-15T10:30:00Z",
                                "redis_error": "Redis connection failed: Connection refused"
                            }
                        }
                    }
                }
            }
        }
    },
    tags=["health"]
)
async def health_check(response: Response) -> HealthCheckResponse:
    """
    Perform health check on service and its dependencies.
    
    Checks PostgreSQL and Redis connectivity with timeout protection.
    Returns detailed status for each component.
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    # Check PostgreSQL with timeout
    postgres_status, postgres_error = run_with_timeout(
        check_postgres, 
        settings.HEALTH_CHECK_TIMEOUT
    )
    
    # Check Redis with timeout
    redis_status, redis_error = run_with_timeout(
        check_redis,
        settings.HEALTH_CHECK_TIMEOUT
    )
    
    # Determine overall health status
    all_healthy = postgres_status == "ok" and redis_status == "ok"
    overall_status = "healthy" if all_healthy else "unhealthy"
    
    # Build response
    health_response = {
        "status": overall_status,
        "postgres": postgres_status,
        "redis": redis_status,
        "timestamp": timestamp
    }
    
    # Add error messages if any checks failed
    if postgres_error:
        health_response["postgres_error"] = postgres_error
    
    if redis_error:
        health_response["redis_error"] = redis_error
    
    # Set appropriate HTTP status code
    if all_healthy:
        response.status_code = status.HTTP_200_OK
    else:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    return health_response
