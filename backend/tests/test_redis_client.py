"""
Tests for redis_client service.
"""
import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock


class TestGetResult:
    """Tests for get_result function."""
    
    @pytest.mark.asyncio
    async def test_returns_parsed_result(self):
        from app.services import redis_client
        
        mock_data = {"status": "completed", "reply": "Hello!"}
        
        with patch.object(redis_client, "redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=json.dumps(mock_data))
            
            result = await redis_client.get_result("req_123")
        
        assert result == mock_data
        assert result["status"] == "completed"
        mock_redis.get.assert_called_once_with("result:req_123")
    
    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        from app.services import redis_client
        
        with patch.object(redis_client, "redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            
            result = await redis_client.get_result("nonexistent")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_uses_correct_key_prefix(self):
        from app.services import redis_client
        
        with patch.object(redis_client, "redis_client") as mock_redis:
            mock_redis.get = AsyncMock(return_value=None)
            
            await redis_client.get_result("my_request_id")
        
        mock_redis.get.assert_called_with("result:my_request_id")


class TestDeleteResult:
    """Tests for delete_result function."""
    
    @pytest.mark.asyncio
    async def test_deletes_with_correct_key(self):
        from app.services import redis_client
        
        with patch.object(redis_client, "redis_client") as mock_redis:
            mock_redis.delete = AsyncMock()
            
            await redis_client.delete_result("req_456")
        
        mock_redis.delete.assert_called_once_with("result:req_456")


class TestConnectRedis:
    """Tests for connect_redis function."""
    
    @pytest.mark.asyncio
    async def test_connects_and_pings(self):
        from app.services import redis_client
        
        with patch("app.services.redis_client.redis.from_url") as mock_from_url:
            mock_client = AsyncMock()
            mock_client.ping = AsyncMock()
            mock_from_url.return_value = mock_client
            
            await redis_client.connect_redis()
        
        mock_client.ping.assert_called_once()


class TestCloseRedis:
    """Tests for close_redis function."""
    
    @pytest.mark.asyncio
    async def test_closes_connection(self):
        from app.services import redis_client
        
        mock_client = AsyncMock()
        mock_client.close = AsyncMock()
        
        with patch.object(redis_client, "redis_client", mock_client):
            await redis_client.close_redis()
        
        mock_client.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handles_none_client(self):
        from app.services import redis_client
        
        with patch.object(redis_client, "redis_client", None):
            # Should not raise error
            await redis_client.close_redis()
