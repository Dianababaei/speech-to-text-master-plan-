"""
API Key Model

This module defines the SQLAlchemy model for API key management.

Table: api_keys
Purpose: Store and manage API keys for authentication and rate limiting

Fields:
- id: Unique identifier for each API key record
- key_hash: Hashed version of the API key (bcrypt/argon2) for secure storage
- project_name: Human-readable identifier for the project/application using this key
- description: Optional detailed description of the key's purpose or usage
- is_active: Flag to enable/disable keys without deletion (soft disable)
- rate_limit: Maximum requests per minute allowed for this key
- created_at: Timestamp of key creation (auto-set)
- updated_at: Timestamp of last modification (auto-updated)
- last_used_at: Timestamp of last successful authentication (nullable, updated on use)

Constraints:
- Unique constraint on key_hash to prevent duplicate keys
- Index on is_active for optimized validation queries
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    Integer,
    DateTime,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import uuid

# Create a base class for declarative models
Base = declarative_base()


class ApiKey(Base):
    """
    SQLAlchemy model for API key storage and management.
    
    This model handles authentication, rate limiting, and usage tracking
    for API access control.
    """
    
    __tablename__ = "api_keys"
    
    # Primary key - UUID for distributed system compatibility
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
        comment="Unique identifier for the API key record"
    )
    
    # Hashed API key - never store plain text keys
    key_hash = Column(
        String(255),
        nullable=False,
        comment="Bcrypt/Argon2 hashed API key for secure storage"
    )
    
    # Project identification
    project_name = Column(
        String(255),
        nullable=False,
        comment="Human-readable project/application identifier"
    )
    
    # Optional project description
    description = Column(
        Text,
        nullable=True,
        comment="Optional detailed description of the key's purpose"
    )
    
    # Active status for soft disable/enable
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Flag to enable/disable the key without deletion"
    )
    
    # Rate limiting configuration
    rate_limit = Column(
        Integer,
        nullable=False,
        comment="Maximum requests per minute allowed for this key"
    )
    
    # Timestamp tracking
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the key was created"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp when the key was last modified"
    )
    
    last_used_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last successful authentication"
    )
    
    # Table-level constraints and indexes
    __table_args__ = (
        # Unique constraint to prevent duplicate key hashes
        UniqueConstraint('key_hash', name='uq_api_keys_key_hash'),
        
        # Index on is_active for fast validation queries
        Index('ix_api_keys_is_active', 'is_active'),
        
        # Table comment
        {'comment': 'Stores API keys with hashing, rate limits, and usage tracking'}
    )
    
    def __repr__(self):
        """
        String representation of the ApiKey model for debugging.
        
        Returns:
            str: A readable representation showing key attributes
        """
        return (
            f"<ApiKey(id={self.id}, "
            f"project_name='{self.project_name}', "
            f"is_active={self.is_active}, "
            f"rate_limit={self.rate_limit}, "
            f"created_at={self.created_at})>"
        )
