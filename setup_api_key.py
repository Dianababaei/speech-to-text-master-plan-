#!/usr/bin/env python3
"""
Script to create an API key for authentication.
Run this after starting the application for the first time.
"""

import uuid
import secrets
from app.database import SessionLocal, init_db
from app.models import APIKey


def generate_api_key() -> str:
    """Generate a secure random API key."""
    return secrets.token_urlsafe(32)


def create_api_key(name: str = "Default API Key", custom_key: str = None) -> str:
    """
    Create a new API key in the database.
    
    Args:
        name: Friendly name for the API key
        custom_key: Optional custom key string (generated if not provided)
    
    Returns:
        The API key string
    """
    # Initialize database
    init_db()
    
    # Create session
    db = SessionLocal()
    
    try:
        # Generate or use provided key
        key_string = custom_key if custom_key else generate_api_key()
        
        # Create API key record
        api_key = APIKey(
            id=str(uuid.uuid4()),
            key=key_string,
            name=name,
            is_active=1
        )
        
        db.add(api_key)
        db.commit()
        db.refresh(api_key)
        
        print("✅ API Key created successfully!")
        print(f"   ID: {api_key.id}")
        print(f"   Name: {api_key.name}")
        print(f"   Key: {api_key.key}")
        print(f"   Created: {api_key.created_at}")
        print("\n⚠️  Save this API key securely - you'll need it for authentication!")
        
        return api_key.key
        
    except Exception as e:
        print(f"❌ Error creating API key: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def list_api_keys():
    """List all API keys in the database."""
    init_db()
    db = SessionLocal()
    
    try:
        api_keys = db.query(APIKey).all()
        
        if not api_keys:
            print("No API keys found in database.")
            return
        
        print(f"\n{'ID':<36} | {'Name':<20} | {'Active':<6} | {'Created'}")
        print("-" * 100)
        
        for key in api_keys:
            active = "Yes" if key.is_active else "No"
            print(f"{key.id:<36} | {key.name:<20} | {active:<6} | {key.created_at}")
        
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("API Key Setup Utility")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            list_api_keys()
        elif sys.argv[1] == "create":
            name = sys.argv[2] if len(sys.argv) > 2 else "API Key"
            create_api_key(name)
        else:
            print("Usage:")
            print("  python setup_api_key.py create [name]  - Create new API key")
            print("  python setup_api_key.py list           - List all API keys")
    else:
        # Default: create a key
        create_api_key()
    
    print("=" * 60)
