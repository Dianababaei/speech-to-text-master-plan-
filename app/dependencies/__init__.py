"""
Dependencies package for FastAPI dependency injection.
"""
from app.dependencies.auth import get_current_api_key

__all__ = ['get_current_api_key']
