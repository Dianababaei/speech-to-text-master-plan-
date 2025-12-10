"""
Redis client configuration.

Centralizes Redis connection setup to avoid circular imports.
"""
import redis
from app.config.settings import get_settings

settings = get_settings()

# Initialize Redis connection pool
redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=settings.HEALTH_CHECK_TIMEOUT,
    socket_timeout=settings.HEALTH_CHECK_TIMEOUT
)
