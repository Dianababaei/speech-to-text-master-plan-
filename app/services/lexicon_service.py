"""
Lexicon service for loading and caching domain-specific terminology.

This service provides the core mechanism for loading lexicon terms with Redis caching
to enable fast, swappable domain-specific lexicons per request.
"""

import json
import logging
from typing import Dict, Optional
from redis import Redis
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.config.settings import get_settings
from app.models.lexicon_term import LexiconTerm

logger = logging.getLogger(__name__)
settings = get_settings()

# Global Redis connection for lexicon caching
_redis_client: Optional[Redis] = None


def get_redis_client() -> Optional[Redis]:
    """
    Get or create Redis client for lexicon caching.
    
    Returns:
        Redis client instance or None if connection fails
    """
    global _redis_client
    
    if _redis_client is None:
        try:
            logger.info(f"Connecting to Redis at {settings.REDIS_URL}")
            _redis_client = Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            _redis_client.ping()
            logger.info("Successfully connected to Redis for lexicon caching")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis for lexicon caching: {e}. Will fallback to database.")
            _redis_client = None
    
    return _redis_client


def _get_cache_key(lexicon_id: str) -> str:
    """
    Generate cache key for a lexicon.
    
    Args:
        lexicon_id: The lexicon identifier
        
    Returns:
        Cache key string
    """
    return f"lexicon:{lexicon_id}"


async def load_lexicon_from_db(db: Session, lexicon_id: str) -> Dict[str, str]:
    """
    Load lexicon terms from database.
    
    Args:
        db: Database session
        lexicon_id: The lexicon identifier to load
        
    Returns:
        Dictionary of {term: replacement} pairs
    """
    try:
        # Query active terms for the specified lexicon
        terms = db.query(LexiconTerm).filter(
            and_(
                LexiconTerm.lexicon_id == lexicon_id,
                LexiconTerm.is_active == True
            )
        ).all()
        
        # Convert to dictionary
        lexicon_dict = {term.term: term.replacement for term in terms}
        
        logger.info(f"Loaded {len(lexicon_dict)} terms for lexicon '{lexicon_id}' from database")
        return lexicon_dict
        
    except Exception as e:
        logger.error(f"Error loading lexicon '{lexicon_id}' from database: {e}")
        raise


async def load_lexicon(db: Session, lexicon_id: str) -> Dict[str, str]:
    """
    Load lexicon terms from cache or database.
    
    This function implements the core caching strategy:
    1. Try to load from Redis cache
    2. If not in cache, load from database
    3. Store in cache for future requests
    4. Fallback to database if Redis is unavailable
    
    Args:
        db: Database session
        lexicon_id: The lexicon identifier to load
        
    Returns:
        Dictionary of {term: replacement} pairs
        
    Raises:
        Exception: If lexicon cannot be loaded from database
    """
    cache_key = _get_cache_key(lexicon_id)
    redis_client = get_redis_client()
    
    # Try to load from cache first
    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.info(f"Cache HIT: Loaded lexicon '{lexicon_id}' from Redis cache")
                return json.loads(cached_data)
            else:
                logger.info(f"Cache MISS: Lexicon '{lexicon_id}' not found in cache")
        except Exception as e:
            logger.warning(f"Error reading from Redis cache: {e}. Falling back to database.")
    
    # Load from database
    lexicon_dict = await load_lexicon_from_db(db, lexicon_id)
    
    # Store in cache for future requests
    if redis_client and lexicon_dict:
        try:
            redis_client.setex(
                cache_key,
                settings.LEXICON_CACHE_TTL,
                json.dumps(lexicon_dict)
            )
            logger.info(
                f"Stored lexicon '{lexicon_id}' in cache "
                f"(TTL: {settings.LEXICON_CACHE_TTL}s, {len(lexicon_dict)} terms)"
            )
        except Exception as e:
            logger.warning(f"Error storing lexicon in Redis cache: {e}")
    
    return lexicon_dict


async def invalidate_lexicon_cache(lexicon_id: str) -> bool:
    """
    Invalidate cached lexicon data.
    
    This function should be called when lexicon terms are modified via CRUD operations:
    - After adding a new term
    - After updating an existing term
    - After deleting (soft delete) a term
    
    Args:
        lexicon_id: The lexicon identifier to invalidate
        
    Returns:
        True if cache was invalidated, False if Redis is unavailable
    """
    cache_key = _get_cache_key(lexicon_id)
    redis_client = get_redis_client()
    
    if redis_client:
        try:
            result = redis_client.delete(cache_key)
            if result:
                logger.info(f"Cache invalidated for lexicon '{lexicon_id}'")
            else:
                logger.info(f"No cache entry found for lexicon '{lexicon_id}' (already expired or never cached)")
            return True
        except Exception as e:
            logger.error(f"Error invalidating cache for lexicon '{lexicon_id}': {e}")
            return False
    else:
        logger.warning(f"Redis unavailable, cannot invalidate cache for lexicon '{lexicon_id}'")
        return False


async def validate_lexicon_exists(db: Session, lexicon_id: str) -> bool:
    """
    Check if a lexicon has any terms in the database.
    
    Args:
        db: Database session
        lexicon_id: The lexicon identifier to check
        
    Returns:
        True if lexicon has at least one active term, False otherwise
    """
    try:
        count = db.query(LexiconTerm).filter(
            and_(
                LexiconTerm.lexicon_id == lexicon_id,
                LexiconTerm.is_active == True
            )
        ).count()
        
        return count > 0
    except Exception as e:
        logger.error(f"Error checking if lexicon '{lexicon_id}' exists: {e}")
        return False


def load_lexicon_sync(db: Session, lexicon_id: str) -> Dict[str, str]:
    """
    Synchronous version of load_lexicon for use in non-async contexts (e.g., workers).
    
    Args:
        db: Database session
        lexicon_id: The lexicon identifier to load
        
    Returns:
        Dictionary of {term: replacement} pairs
    """
    cache_key = _get_cache_key(lexicon_id)
    redis_client = get_redis_client()
    
    # Try to load from cache first
    if redis_client:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                logger.info(f"Cache HIT: Loaded lexicon '{lexicon_id}' from Redis cache")
                return json.loads(cached_data)
            else:
                logger.info(f"Cache MISS: Lexicon '{lexicon_id}' not found in cache")
        except Exception as e:
            logger.warning(f"Error reading from Redis cache: {e}. Falling back to database.")
    
    # Load from database
    try:
        terms = db.query(LexiconTerm).filter(
            and_(
                LexiconTerm.lexicon_id == lexicon_id,
                LexiconTerm.is_active == True
            )
        ).all()
        
        lexicon_dict = {term.term: term.replacement for term in terms}
        logger.info(f"Loaded {len(lexicon_dict)} terms for lexicon '{lexicon_id}' from database")
        
        # Store in cache
        if redis_client and lexicon_dict:
            try:
                redis_client.setex(
                    cache_key,
                    settings.LEXICON_CACHE_TTL,
                    json.dumps(lexicon_dict)
                )
                logger.info(f"Stored lexicon '{lexicon_id}' in cache")
            except Exception as e:
                logger.warning(f"Error storing lexicon in Redis cache: {e}")
        
        return lexicon_dict
        
    except Exception as e:
        logger.error(f"Error loading lexicon '{lexicon_id}' from database: {e}")
        raise
