#!/usr/bin/env python
"""
CLI utility to create API keys.

This script provides a command-line interface for administrators to
generate new API keys without using the HTTP API.

Usage:
    python create_api_key.py --project "My Project" --rate-limit 1000

    python create_api_key.py --project "Test App" --description "Development key"
"""

import argparse
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.services.api_key_service import create_api_key, APIKeyError
from app.config.settings import get_settings


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate a new API key for the transcription service"
    )
    parser.add_argument(
        "--project",
        "-p",
        required=True,
        help="Project name (required)"
    )
    parser.add_argument(
        "--description",
        "-d",
        help="Optional description of the key's purpose"
    )
    parser.add_argument(
        "--rate-limit",
        "-r",
        type=int,
        default=100,
        help="Maximum requests per minute (default: 100)"
    )

    args = parser.parse_args()

    # Get database connection
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Create API key
        print(f"\nGenerating API key for project: {args.project}")
        print(f"Rate limit: {args.rate_limit} requests/minute\n")

        plaintext_key, api_key_record = create_api_key(
            db=db,
            project_name=args.project,
            description=args.description,
            rate_limit=args.rate_limit
        )

        # Display results
        print("=" * 80)
        print("API KEY GENERATED SUCCESSFULLY")
        print("=" * 80)
        print(f"\nAPI Key ID:    {api_key_record.id}")
        print(f"Project:       {api_key_record.project_name}")
        print(f"Rate Limit:    {api_key_record.rate_limit} requests/minute")
        print(f"Created:       {api_key_record.created_at}")
        print(f"\n{'!' * 80}")
        print("IMPORTANT: Save this API key now - it will NEVER be shown again!")
        print(f"{'!' * 80}")
        print(f"\nAPI Key: {plaintext_key}\n")
        print("=" * 80)

    except APIKeyError as e:
        print(f"\n❌ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
