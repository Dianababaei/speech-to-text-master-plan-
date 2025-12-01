from datetime import datetime
from fastapi import APIRouter, Response, status
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, TimeoutError as SQLTimeoutError
import redis
from app.database import engine
from app.main import redis_client
from app.config.settings import settings
import asyncio
from concurrent.futures import TimeoutError
import signal

router = APIRouter(tags=["health"])


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


@router.get("/health")
async def health_check(response: Response):
    """
    Health check endpoint that verifies connectivity to all critical dependencies.
    
    Checks:
    - PostgreSQL database connection
    - Redis connection
    
    Returns:
        JSON response with overall status and individual component statuses.
        
    Status Codes:
        200: All dependencies are healthy
        503: One or more dependencies are unhealthy
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
