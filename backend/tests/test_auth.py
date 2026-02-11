"""
Tests for auth service.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
from jose import jwt

from app.services.auth import (
    create_access_token,
    get_current_user,
    get_or_create_user,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_DAYS,
)


class TestCreateAccessToken:
    """Tests for create_access_token function."""
    
    def test_creates_valid_jwt(self):
        email = "test@example.com"
        
        with patch("app.services.auth.settings") as mock_settings:
            mock_settings.SECRET_KEY = "test_secret_key_12345"
            token = create_access_token(email)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_token_contains_email(self):
        email = "user@example.com"
        
        with patch("app.services.auth.settings") as mock_settings:
            mock_settings.SECRET_KEY = "test_secret_key_12345"
            token = create_access_token(email)
            
            # Decode token
            payload = jwt.decode(token, "test_secret_key_12345", algorithms=[ALGORITHM])
        
        assert payload["sub"] == email
    
    def test_token_has_expiration(self):
        email = "test@example.com"
        
        with patch("app.services.auth.settings") as mock_settings:
            mock_settings.SECRET_KEY = "test_secret_key_12345"
            token = create_access_token(email)
            
            payload = jwt.decode(token, "test_secret_key_12345", algorithms=[ALGORITHM])
        
        assert "exp" in payload
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        now = datetime.utcnow()
        
        # Expiration should be approximately ACCESS_TOKEN_EXPIRE_DAYS in the future
        diff = exp_time - now
        assert diff.days >= ACCESS_TOKEN_EXPIRE_DAYS - 1
        assert diff.days <= ACCESS_TOKEN_EXPIRE_DAYS


class TestGetCurrentUser:
    """Tests for get_current_user function."""
    
    @pytest.mark.asyncio
    async def test_returns_user_for_valid_token(self, mock_user):
        with patch("app.services.auth.settings") as mock_settings:
            mock_settings.SECRET_KEY = "test_secret_key_12345"
            
            # Create valid token
            token = create_access_token(mock_user["email"])
            
            # Mock database
            with patch("app.services.auth.get_db") as mock_get_db:
                mock_db = MagicMock()
                mock_db.users.find_one = AsyncMock(return_value=mock_user)
                mock_get_db.return_value = mock_db
                
                result = await get_current_user(token)
        
        assert result is not None
        assert result["email"] == mock_user["email"]
    
    @pytest.mark.asyncio
    async def test_returns_none_for_invalid_token(self):
        with patch("app.services.auth.settings") as mock_settings:
            mock_settings.SECRET_KEY = "test_secret_key_12345"
            
            result = await get_current_user("invalid_token_here")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_returns_none_for_expired_token(self):
        with patch("app.services.auth.settings") as mock_settings:
            mock_settings.SECRET_KEY = "test_secret_key_12345"
            
            # Create expired token
            expire = datetime.utcnow() - timedelta(days=1)
            payload = {"sub": "test@example.com", "exp": expire}
            token = jwt.encode(payload, "test_secret_key_12345", algorithm=ALGORITHM)
            
            result = await get_current_user(token)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_returns_none_when_user_not_found(self):
        with patch("app.services.auth.settings") as mock_settings:
            mock_settings.SECRET_KEY = "test_secret_key_12345"
            
            token = create_access_token("nonexistent@example.com")
            
            with patch("app.services.auth.get_db") as mock_get_db:
                mock_db = MagicMock()
                mock_db.users.find_one = AsyncMock(return_value=None)
                mock_get_db.return_value = mock_db
                
                result = await get_current_user(token)
        
        assert result is None


class TestGetOrCreateUser:
    """Tests for get_or_create_user function."""
    
    @pytest.mark.asyncio
    async def test_returns_existing_user(self, mock_user):
        user_info = {
            "email": mock_user["email"],
            "name": "Updated Name",
            "picture": "new_picture.jpg",
            "google_id": "google_456",
        }
        
        with patch("app.services.auth.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_db.users.find_one = AsyncMock(return_value=mock_user)
            mock_db.users.update_one = AsyncMock()
            mock_get_db.return_value = mock_db
            
            result = await get_or_create_user(user_info)
        
        assert result["email"] == mock_user["email"]
        mock_db.users.update_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_creates_new_user(self):
        user_info = {
            "email": "new@example.com",
            "name": "New User",
            "picture": "picture.jpg",
            "google_id": "google_new",
        }
        
        with patch("app.services.auth.get_db") as mock_get_db:
            mock_db = MagicMock()
            # First find returns None (user doesn't exist)
            # Second find returns the created user
            mock_db.users.find_one = AsyncMock(side_effect=[
                None,  # First call - user doesn't exist
                {**user_info, "_id": "new_id"},  # After insert
            ])
            mock_db.users.insert_one = AsyncMock(return_value=MagicMock(inserted_id="new_id"))
            mock_get_db.return_value = mock_db
            
            result = await get_or_create_user(user_info)
        
        assert result["email"] == user_info["email"]
        mock_db.users.insert_one.assert_called_once()
