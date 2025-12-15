"""
Unit tests for authentication logic.

Tests cover:
- API key validation (get_api_key dependency)
- Admin API key validation (get_admin_api_key dependency)
- Error handling for missing/invalid keys
- Active/inactive key handling
- Admin privilege checking
"""
import pytest

pytestmark = [pytest.mark.unit, pytest.mark.auth]
from unittest.mock import Mock, AsyncMock, MagicMock
from fastapi import HTTPException

from app.auth import get_api_key, get_admin_api_key


class TestGetApiKey:
    """Test API key validation logic."""
    
    @pytest.mark.asyncio
    async def test_valid_active_api_key(self, mock_db_session, mock_api_key):
        """Test validation with valid, active API key."""
        # Mock database query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_api_key
        mock_db_session.query.return_value = mock_query
        
        result = await get_api_key(
            x_api_key="test-api-key-12345",
            db=mock_db_session
        )
        
        assert result == mock_api_key
        assert result.is_active is True
    
    @pytest.mark.asyncio
    async def test_missing_api_key_header(self, mock_db_session):
        """Test that missing API key raises 401."""
        with pytest.raises(HTTPException) as exc_info:
            await get_api_key(x_api_key=None, db=mock_db_session)
        
        assert exc_info.value.status_code == 401
        assert "API key is required" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_invalid_api_key(self, mock_db_session):
        """Test that invalid API key raises 401."""
        # Mock database query returning None
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query
        
        with pytest.raises(HTTPException) as exc_info:
            await get_api_key(
                x_api_key="invalid-key",
                db=mock_db_session
            )
        
        assert exc_info.value.status_code == 401
        assert "Invalid or inactive" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_inactive_api_key(self, mock_db_session):
        """Test that inactive API key raises 401."""
        inactive_key = Mock()
        inactive_key.key = "test-api-key"
        inactive_key.is_active = False
        
        # Mock database query
        mock_query = Mock()
        # The query filters for is_active == 1, so it should return None for inactive
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query
        
        with pytest.raises(HTTPException) as exc_info:
            await get_api_key(
                x_api_key="test-api-key",
                db=mock_db_session
            )
        
        assert exc_info.value.status_code == 401
        assert "Invalid or inactive" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_empty_string_api_key(self, mock_db_session):
        """Test that empty string API key raises 401."""
        with pytest.raises(HTTPException) as exc_info:
            await get_api_key(x_api_key="", db=mock_db_session)
        
        assert exc_info.value.status_code == 401
        assert "API key is required" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_database_query_structure(self, mock_db_session, mock_api_key):
        """Test that database query filters correctly."""
        # Mock database query
        mock_filter = Mock()
        mock_filter.first.return_value = mock_api_key
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_filter
        
        mock_db_session.query.return_value = mock_query
        
        result = await get_api_key(
            x_api_key="test-api-key-12345",
            db=mock_db_session
        )
        
        assert result == mock_api_key
        # Verify query was called
        mock_db_session.query.assert_called_once()


class TestGetAdminApiKey:
    """Test admin API key validation logic."""
    
    @pytest.mark.asyncio
    async def test_valid_admin_key_with_role_metadata(self, mock_admin_api_key):
        """Test validation with valid admin key (role in metadata)."""
        mock_admin_api_key.metadata = {"role": "admin"}
        mock_admin_api_key.project_name = "test-project"
        
        result = await get_admin_api_key(api_key=mock_admin_api_key)
        
        assert result == mock_admin_api_key
    
    @pytest.mark.asyncio
    async def test_valid_admin_key_with_admin_project_name(self, mock_api_key):
        """Test validation with admin in project name."""
        mock_api_key.project_name = "admin-project"
        mock_api_key.metadata = {}
        
        result = await get_admin_api_key(api_key=mock_api_key)
        
        assert result == mock_api_key
    
    @pytest.mark.asyncio
    async def test_valid_admin_key_case_insensitive_project_name(self, mock_api_key):
        """Test that project name check is case-insensitive."""
        mock_api_key.project_name = "ADMIN-Project"
        mock_api_key.metadata = {}
        
        result = await get_admin_api_key(api_key=mock_api_key)
        
        assert result == mock_api_key
    
    @pytest.mark.asyncio
    async def test_non_admin_key_raises_403(self, mock_api_key):
        """Test that non-admin key raises 403."""
        mock_api_key.project_name = "regular-project"
        mock_api_key.metadata = {}
        
        with pytest.raises(HTTPException) as exc_info:
            await get_admin_api_key(api_key=mock_api_key)
        
        assert exc_info.value.status_code == 403
        assert "Admin privileges required" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_admin_key_with_non_admin_metadata(self, mock_api_key):
        """Test key with metadata but non-admin role."""
        mock_api_key.project_name = "regular-project"
        mock_api_key.metadata = {"role": "user"}
        
        with pytest.raises(HTTPException) as exc_info:
            await get_admin_api_key(api_key=mock_api_key)
        
        assert exc_info.value.status_code == 403
    
    @pytest.mark.asyncio
    async def test_admin_key_with_null_metadata(self, mock_api_key):
        """Test key with null metadata and non-admin project name."""
        mock_api_key.project_name = "regular-project"
        mock_api_key.metadata = None
        
        with pytest.raises(HTTPException) as exc_info:
            await get_admin_api_key(api_key=mock_api_key)
        
        assert exc_info.value.status_code == 403
    
    @pytest.mark.asyncio
    async def test_admin_key_with_empty_metadata(self, mock_api_key):
        """Test key with empty metadata dict."""
        mock_api_key.project_name = "regular-project"
        mock_api_key.metadata = {}
        
        with pytest.raises(HTTPException) as exc_info:
            await get_admin_api_key(api_key=mock_api_key)
        
        assert exc_info.value.status_code == 403
    
    @pytest.mark.asyncio
    async def test_admin_key_with_partial_match_in_project_name(self, mock_api_key):
        """Test that 'admin' substring in project name grants access."""
        test_cases = [
            "admin-dashboard",
            "system-admin",
            "administrator-portal",
            "ADMIN"
        ]
        
        for project_name in test_cases:
            mock_api_key.project_name = project_name
            mock_api_key.metadata = {}
            
            result = await get_admin_api_key(api_key=mock_api_key)
            assert result == mock_api_key
    
    @pytest.mark.asyncio
    async def test_admin_check_with_non_dict_metadata(self, mock_api_key):
        """Test handling of non-dict metadata (edge case)."""
        mock_api_key.project_name = "regular-project"
        mock_api_key.metadata = "not-a-dict"  # Invalid metadata type
        
        with pytest.raises(HTTPException) as exc_info:
            await get_admin_api_key(api_key=mock_api_key)
        
        assert exc_info.value.status_code == 403


class TestAuthenticationFlow:
    """Test complete authentication flows."""
    
    @pytest.mark.asyncio
    async def test_regular_user_flow(self, mock_db_session, mock_api_key):
        """Test complete flow for regular user authentication."""
        # Step 1: Validate API key
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_api_key
        mock_db_session.query.return_value = mock_query
        
        api_key = await get_api_key(
            x_api_key="test-api-key-12345",
            db=mock_db_session
        )
        
        assert api_key.is_active is True
        
        # Step 2: Try admin endpoint (should fail)
        api_key.project_name = "regular-project"
        api_key.metadata = {}
        
        with pytest.raises(HTTPException) as exc_info:
            await get_admin_api_key(api_key=api_key)
        
        assert exc_info.value.status_code == 403
    
    @pytest.mark.asyncio
    async def test_admin_user_flow(self, mock_db_session, mock_admin_api_key):
        """Test complete flow for admin user authentication."""
        # Step 1: Validate API key
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_admin_api_key
        mock_db_session.query.return_value = mock_query
        
        api_key = await get_api_key(
            x_api_key="admin-api-key-67890",
            db=mock_db_session
        )
        
        assert api_key.is_active is True
        
        # Step 2: Verify admin privileges
        admin_key = await get_admin_api_key(api_key=api_key)
        
        assert admin_key == mock_admin_api_key
        assert admin_key.metadata["role"] == "admin"
    
    @pytest.mark.asyncio
    async def test_invalid_then_valid_key(self, mock_db_session, mock_api_key):
        """Test attempting invalid key then valid key."""
        # First attempt with invalid key
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query
        
        with pytest.raises(HTTPException) as exc_info:
            await get_api_key(
                x_api_key="invalid-key",
                db=mock_db_session
            )
        
        assert exc_info.value.status_code == 401
        
        # Second attempt with valid key
        mock_query.filter.return_value.first.return_value = mock_api_key
        
        result = await get_api_key(
            x_api_key="test-api-key-12345",
            db=mock_db_session
        )
        
        assert result == mock_api_key


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    @pytest.mark.asyncio
    async def test_very_long_api_key(self, mock_db_session):
        """Test handling of very long API key strings."""
        long_key = "a" * 1000
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query
        
        with pytest.raises(HTTPException) as exc_info:
            await get_api_key(x_api_key=long_key, db=mock_db_session)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_special_characters_in_api_key(self, mock_db_session, mock_api_key):
        """Test API key with special characters."""
        special_key = "key-with-special!@#$%^&*()_+="
        mock_api_key.key = special_key
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_api_key
        mock_db_session.query.return_value = mock_query
        
        result = await get_api_key(x_api_key=special_key, db=mock_db_session)
        
        assert result == mock_api_key
    
    @pytest.mark.asyncio
    async def test_whitespace_in_api_key(self, mock_db_session):
        """Test API key with whitespace."""
        # API key with spaces should be treated as-is (no trimming in auth)
        key_with_spaces = " test-api-key "
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query
        
        with pytest.raises(HTTPException) as exc_info:
            await get_api_key(x_api_key=key_with_spaces, db=mock_db_session)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_unicode_in_project_name(self, mock_api_key):
        """Test project name with Unicode characters."""
        mock_api_key.project_name = "مدیر-admin-проект"
        mock_api_key.metadata = {}
        
        # Should still detect 'admin' substring
        result = await get_admin_api_key(api_key=mock_api_key)
        assert result == mock_api_key
    
    @pytest.mark.asyncio
    async def test_null_project_name(self, mock_api_key):
        """Test handling of null project name."""
        mock_api_key.project_name = None
        mock_api_key.metadata = {"role": "admin"}
        
        # Should still work with admin role in metadata
        result = await get_admin_api_key(api_key=mock_api_key)
        assert result == mock_api_key
    
    @pytest.mark.asyncio
    async def test_empty_project_name(self, mock_api_key):
        """Test handling of empty project name."""
        mock_api_key.project_name = ""
        mock_api_key.metadata = {}
        
        with pytest.raises(HTTPException) as exc_info:
            await get_admin_api_key(api_key=mock_api_key)
        
        assert exc_info.value.status_code == 403
