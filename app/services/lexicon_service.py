"""
Lexicon Service

This module provides business logic for lexicon discovery and metadata retrieval,
including database aggregation queries and Redis caching.
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
import redis

from app.models.lexicon import LexiconTerm, LexiconMetadata
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Redis client for caching
redis_client = None

# Lexicon descriptions (can be moved to config/database later)
LEXICON_DESCRIPTIONS = {
    "radiology": "Medical radiology terminology",
    "cardiology": "Cardiovascular and cardiac terminology",
    "general": "General medical terminology",
}

# Cache configuration
CACHE_TTL_SECONDS = 600  # 10 minutes
CACHE_KEY_ALL_LEXICONS = "lexicons:all"
CACHE_KEY_LEXICON_PREFIX = "lexicons:detail:"


def get_redis_client() -> redis.Redis:
    """
    Get or create Redis client.
    
    Returns:
        redis.Redis: Redis client instance
    """
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
    return redis_client


def get_all_lexicons(db: Session, use_cache: bool = True) -> List[LexiconMetadata]:
    """
    Get metadata for all available lexicons.
    
    Queries the lexicon_terms table, groups by lexicon_id, counts active terms,
    and retrieves the most recent update timestamp for each lexicon.
    
    Args:
        db: Database session
        use_cache: Whether to use Redis cache (default: True)
    
    Returns:
        List[LexiconMetadata]: List of lexicon metadata objects
    """
    # Try to get from cache first
    if use_cache:
        try:
            cache = get_redis_client()
            cached_data = cache.get(CACHE_KEY_ALL_LEXICONS)
            if cached_data:
                logger.debug("Cache hit for all lexicons")
                data = json.loads(cached_data)
                return [
                    LexiconMetadata(
                        lexicon_id=item["lexicon_id"],
                        term_count=item["term_count"],
                        last_updated=datetime.fromisoformat(item["last_updated"]),
                        description=item.get("description")
                    )
                    for item in data
                ]
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
    
    # Query database
    logger.debug("Querying database for all lexicons")
    
    # Aggregate query: group by lexicon_id, count active terms, get max updated_at
    results = db.query(
        LexiconTerm.lexicon_id,
        func.count(LexiconTerm.id).label('term_count'),
        func.max(LexiconTerm.updated_at).label('last_updated')
    ).filter(
        LexiconTerm.is_active == True,
        LexiconTerm.lexicon_id.isnot(None)  # Only include terms with lexicon_id set
    ).group_by(
        LexiconTerm.lexicon_id
    ).all()
    
    # Convert to LexiconMetadata objects
    lexicons = []
    for result in results:
        lexicon_id = result.lexicon_id
        lexicons.append(
            LexiconMetadata(
                lexicon_id=lexicon_id,
                term_count=result.term_count,
                last_updated=result.last_updated,
                description=LEXICON_DESCRIPTIONS.get(lexicon_id)
            )
        )
    
    # Cache the results
    if use_cache and lexicons:
        try:
            cache = get_redis_client()
            cache_data = [
                {
                    "lexicon_id": lex.lexicon_id,
                    "term_count": lex.term_count,
                    "last_updated": lex.last_updated.isoformat(),
                    "description": lex.description
                }
                for lex in lexicons
            ]
            cache.setex(
                CACHE_KEY_ALL_LEXICONS,
                CACHE_TTL_SECONDS,
                json.dumps(cache_data)
            )
            logger.debug("Cached all lexicons metadata")
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
    
    return lexicons


def get_lexicon_by_id(db: Session, lexicon_id: str, use_cache: bool = True) -> Optional[LexiconMetadata]:
    """
    Get metadata for a specific lexicon.
    
    Args:
        db: Database session
        lexicon_id: Unique lexicon identifier
        use_cache: Whether to use Redis cache (default: True)
    
    Returns:
        Optional[LexiconMetadata]: Lexicon metadata or None if not found
    """
    cache_key = f"{CACHE_KEY_LEXICON_PREFIX}{lexicon_id}"
    
    # Try to get from cache first
    if use_cache:
        try:
            cache = get_redis_client()
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for lexicon {lexicon_id}")
                data = json.loads(cached_data)
                return LexiconMetadata(
                    lexicon_id=data["lexicon_id"],
                    term_count=data["term_count"],
                    last_updated=datetime.fromisoformat(data["last_updated"]),
                    description=data.get("description")
                )
        except Exception as e:
            logger.warning(f"Cache read error for {lexicon_id}: {e}")
    
    # Query database
    logger.debug(f"Querying database for lexicon {lexicon_id}")
    
    result = db.query(
        LexiconTerm.lexicon_id,
        func.count(LexiconTerm.id).label('term_count'),
        func.max(LexiconTerm.updated_at).label('last_updated')
    ).filter(
        LexiconTerm.is_active == True,
        LexiconTerm.lexicon_id == lexicon_id
    ).group_by(
        LexiconTerm.lexicon_id
    ).first()
    
    if not result or result.term_count == 0:
        return None
    
    # Convert to LexiconMetadata
    lexicon = LexiconMetadata(
        lexicon_id=result.lexicon_id,
        term_count=result.term_count,
        last_updated=result.last_updated,
        description=LEXICON_DESCRIPTIONS.get(lexicon_id)
    )
    
    # Cache the result
    if use_cache:
        try:
            cache = get_redis_client()
            cache_data = {
                "lexicon_id": lexicon.lexicon_id,
                "term_count": lexicon.term_count,
                "last_updated": lexicon.last_updated.isoformat(),
                "description": lexicon.description
            }
            cache.setex(
                cache_key,
                CACHE_TTL_SECONDS,
                json.dumps(cache_data)
            )
            logger.debug(f"Cached metadata for lexicon {lexicon_id}")
        except Exception as e:
            logger.warning(f"Cache write error for {lexicon_id}: {e}")
    
    return lexicon


def invalidate_lexicon_cache(lexicon_id: Optional[str] = None) -> None:
    """
    Invalidate lexicon metadata cache.
    
    Should be called when lexicon terms are added, updated, or deleted.
    
    Args:
        lexicon_id: Specific lexicon to invalidate, or None to invalidate all
    """
    try:
        cache = get_redis_client()
        
        if lexicon_id:
            # Invalidate specific lexicon
            cache_key = f"{CACHE_KEY_LEXICON_PREFIX}{lexicon_id}"
            cache.delete(cache_key)
            logger.info(f"Invalidated cache for lexicon {lexicon_id}")
        
        # Always invalidate the all-lexicons cache
        cache.delete(CACHE_KEY_ALL_LEXICONS)
        logger.info("Invalidated all lexicons cache")
        
    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")


def invalidate_all_lexicon_caches() -> None:
    """
    Invalidate all lexicon-related caches.
    
    Use this for bulk operations or when unsure which lexicons were affected.
    """
    try:
        cache = get_redis_client()
        
        # Delete the all-lexicons cache
        cache.delete(CACHE_KEY_ALL_LEXICONS)
        
        # Delete all individual lexicon caches using pattern matching
        pattern = f"{CACHE_KEY_LEXICON_PREFIX}*"
        cursor = 0
        while True:
            cursor, keys = cache.scan(cursor, match=pattern, count=100)
            if keys:
                cache.delete(*keys)
            if cursor == 0:
                break
        
        logger.info("Invalidated all lexicon caches")
        
    except Exception as e:
        logger.error(f"Error invalidating all caches: {e}")
