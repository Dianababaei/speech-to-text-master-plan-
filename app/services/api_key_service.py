"""
API Key generation, hashing, and validation service.

This module provides secure API key management functionality including:
- Cryptographically secure key generation
- Bcrypt-based key hashing for secure storage
- Key verification against stored hashes
- Database operations for API key creation
"""

import secrets
from typing import Optional, Tuple
from datetime import datetime

from passlib.hash import bcrypt
from sqlalchemy.orm import Session

from app.models.api_key import ApiKey


class APIKeyError(Exception):
    """Base exception for API key service errors."""
    pass


class APIKeyValidationError(APIKeyError):
    """Raised when API key validation fails."""
    pass


class APIKeyStorageError(APIKeyError):
    """Raised when API key storage operations fail."""
    pass


def generate_api_key() -> str:
    """
    Generate a cryptographically secure API key.

    Uses secrets.token_urlsafe to generate a 32-byte random key
    that is URL-safe and suitable for use as an API key.

    Returns:
        str: A secure, URL-safe API key (base64-encoded, approximately 43 characters)

    Example:
        >>> key = generate_api_key()
        >>> len(key) >= 43
        True
    """
    return secrets.token_urlsafe(32)


def hash_api_key(key: str) -> str:
    """
    Hash an API key using bcrypt for secure storage.

    Args:
        key: Plain text API key to hash

    Returns:
        str: Bcrypt hash of the API key

    Raises:
        APIKeyError: If hashing fails

    Example:
        >>> key = "test_key_12345"
        >>> hash_value = hash_api_key(key)
        >>> hash_value.startswith("$2b$")
        True
    """
    try:
        return bcrypt.hash(key)
    except Exception as e:
        raise APIKeyError(f"Failed to hash API key: {str(e)}")


def verify_api_key(plain_key: str, key_hash: str) -> bool:
    """
    Verify a plain text API key against a stored hash.

    Args:
        plain_key: Plain text API key to verify
        key_hash: Bcrypt hash to verify against

    Returns:
        bool: True if the key matches the hash, False otherwise

    Raises:
        APIKeyValidationError: If verification process fails

    Example:
        >>> key = "test_key_12345"
        >>> hash_value = hash_api_key(key)
        >>> verify_api_key(key, hash_value)
        True
        >>> verify_api_key("wrong_key", hash_value)
        False
    """
    try:
        return bcrypt.verify(plain_key, key_hash)
    except Exception as e:
        raise APIKeyValidationError(f"Failed to verify API key: {str(e)}")


def create_api_key(
    db: Session,
    project_name: str,
    description: Optional[str] = None,
    rate_limit: int = 100
) -> Tuple[str, ApiKey]:
    """
    Create a new API key and store it in the database.

    This function:
    1. Generates a new cryptographically secure API key
    2. Hashes it using bcrypt
    3. Stores the hash in the database with metadata
    4. Returns the plaintext key (only time it's available) and the database record

    Args:
        db: Database session
        project_name: Human-readable identifier for the project/application
        description: Optional detailed description of the key's purpose
        rate_limit: Maximum requests per minute (default: 100)

    Returns:
        Tuple[str, ApiKey]: (plaintext_api_key, api_key_record)

    Raises:
        APIKeyStorageError: If database operation fails
        APIKeyError: If key generation or hashing fails

    Example:
        >>> from app.database import get_db
        >>> db = next(get_db())
        >>> plaintext_key, api_key_record = create_api_key(
        ...     db=db,
        ...     project_name="My Project",
        ...     description="Production API key",
        ...     rate_limit=1000
        ... )
        >>> print(f"Save this key: {plaintext_key}")
        >>> print(f"Key ID: {api_key_record.id}")
    """
    # Validate input
    if not project_name or not project_name.strip():
        raise APIKeyValidationError("project_name is required and cannot be empty")

    if rate_limit <= 0:
        raise APIKeyValidationError("rate_limit must be greater than 0")

    try:
        # Generate new API key
        plaintext_key = generate_api_key()

        # Hash the key for storage
        key_hash = hash_api_key(plaintext_key)

        # Create database record
        api_key = ApiKey(
            key_hash=key_hash,
            project_name=project_name.strip(),
            description=description.strip() if description else None,
            is_active=True,
            rate_limit=rate_limit,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Save to database
        db.add(api_key)
        db.commit()
        db.refresh(api_key)

        return plaintext_key, api_key

    except APIKeyError:
        # Re-raise API key specific errors
        db.rollback()
        raise
    except Exception as e:
        # Catch database and other errors
        db.rollback()
        raise APIKeyStorageError(f"Failed to create API key: {str(e)}")


def get_api_key_by_hash(db: Session, key_hash: str) -> Optional[ApiKey]:
    """
    Retrieve an API key record by its hash.

    Args:
        db: Database session
        key_hash: The bcrypt hash to search for

    Returns:
        Optional[ApiKey]: The API key record if found, None otherwise
    """
    return db.query(ApiKey).filter(ApiKey.key_hash == key_hash).first()


def get_api_key_by_id(db: Session, key_id: str) -> Optional[ApiKey]:
    """
    Retrieve an API key record by its ID.

    Args:
        db: Database session
        key_id: The UUID of the API key

    Returns:
        Optional[ApiKey]: The API key record if found, None otherwise
    """
    return db.query(ApiKey).filter(ApiKey.id == key_id).first()


def validate_and_get_api_key(db: Session, plaintext_key: str) -> Optional[ApiKey]:
    """
    Validate a plaintext API key and return the associated record if valid.

    This function searches all active API keys and verifies the plaintext key
    against their hashes. This is intentionally slower to prevent timing attacks.

    Args:
        db: Database session
        plaintext_key: The plaintext API key to validate

    Returns:
        Optional[ApiKey]: The API key record if valid and active, None otherwise

    Note:
        This function updates the last_used_at timestamp for valid keys.
    """
    # Get all active API keys
    active_keys = db.query(ApiKey).filter(ApiKey.is_active == True).all()

    for api_key in active_keys:
        try:
            if verify_api_key(plaintext_key, api_key.key_hash):
                # Update last used timestamp
                api_key.last_used_at = datetime.utcnow()
                db.commit()
                return api_key
        except APIKeyValidationError:
            # Continue checking other keys if verification fails
            continue

    return None


def deactivate_api_key(db: Session, key_id: str) -> bool:
    """
    Deactivate an API key (soft delete).

    Args:
        db: Database session
        key_id: UUID of the API key to deactivate

    Returns:
        bool: True if key was deactivated, False if not found

    Raises:
        APIKeyStorageError: If database operation fails
    """
    try:
        api_key = get_api_key_by_id(db, key_id)

        if not api_key:
            return False

        api_key.is_active = False
        api_key.updated_at = datetime.utcnow()
        db.commit()

        return True

    except Exception as e:
        db.rollback()
        raise APIKeyStorageError(f"Failed to deactivate API key: {str(e)}")
