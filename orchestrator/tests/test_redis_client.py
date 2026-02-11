"""
Tests for redis_client service.
"""
import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock


class TestStreamUpdate:
    """Tests for stream_update function."""
    
    @pytest.mark.asyncio
    async def test_updates_redis_with_content(self):
        """Should update Redis with streaming content."""
        from app.services import redis_client
        
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()
        
        with patch.object(redis_client, "redis_client", mock_redis):
            with patch.object(redis_client, "settings") as mock_settings:
                mock_settings.REDIS_RESULT_TTL = 300
                
                await redis_client.stream_update("req_123", "Hello", finished=0)
        
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        
        assert call_args[0][0] == "result:req_123"
        
        # Parse the stored JSON
        stored_data = json.loads(call_args[0][2])
        assert stored_data["reply"] == "Hello"
        assert stored_data["finished"] == 0
    
    @pytest.mark.asyncio
    async def test_sets_finished_flag(self):
        """Should set finished flag when complete."""
        from app.services import redis_client
        
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()
        
        with patch.object(redis_client, "redis_client", mock_redis):
            with patch.object(redis_client, "settings") as mock_settings:
                mock_settings.REDIS_RESULT_TTL = 300
                
                await redis_client.stream_update("req_123", "Complete response", finished=1)
        
        stored_data = json.loads(mock_redis.setex.call_args[0][2])
        assert stored_data["finished"] == 1


class TestSetResult:
    """Tests for set_result function."""
    
    @pytest.mark.asyncio
    async def test_stores_result_with_ttl(self):
        """Should store result with TTL."""
        from app.services import redis_client
        
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()
        
        with patch.object(redis_client, "redis_client", mock_redis):
            with patch.object(redis_client, "settings") as mock_settings:
                mock_settings.REDIS_RESULT_TTL = 300
                
                await redis_client.set_result("req_123", {
                    "status": "completed",
                    "reply": "Response",
                })
        
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        
        assert call_args[0][0] == "result:req_123"
        assert call_args[0][1] == 300  # TTL
    
    @pytest.mark.asyncio
    async def test_serializes_result_to_json(self):
        """Should serialize result to JSON."""
        from app.services import redis_client
        
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()
        
        with patch.object(redis_client, "redis_client", mock_redis):
            with patch.object(redis_client, "settings") as mock_settings:
                mock_settings.REDIS_RESULT_TTL = 300
                
                await redis_client.set_result("req_123", {"key": "value"})
        
        stored_value = mock_redis.setex.call_args[0][2]
        parsed = json.loads(stored_value)
        assert parsed["key"] == "value"


class TestSetError:
    """Tests for set_error function."""
    
    @pytest.mark.asyncio
    async def test_stores_error_with_status(self):
        """Should store error with error status."""
        from app.services import redis_client
        
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()
        
        with patch.object(redis_client, "redis_client", mock_redis):
            with patch.object(redis_client, "settings") as mock_settings:
                mock_settings.REDIS_RESULT_TTL = 300
                
                await redis_client.set_error("req_123", "Something went wrong")
        
        stored_data = json.loads(mock_redis.setex.call_args[0][2])
        assert stored_data["status"] == "error"
        assert stored_data["error"] == "Something went wrong"
        assert stored_data["finished"] == 1


class TestGetResult:
    """Tests for get_result function."""
    
    @pytest.mark.asyncio
    async def test_returns_parsed_result(self):
        """Should return parsed result from Redis."""
        from app.services import redis_client
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=json.dumps({
            "status": "completed",
            "reply": "Hello",
        }))
        
        with patch.object(redis_client, "redis_client", mock_redis):
            result = await redis_client.get_result("req_123")
        
        assert result["status"] == "completed"
        assert result["reply"] == "Hello"
    
    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        """Should return None when key not found."""
        from app.services import redis_client
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        
        with patch.object(redis_client, "redis_client", mock_redis):
            result = await redis_client.get_result("nonexistent")
        
        assert result is None


class TestConnectRedis:
    """Tests for connect_redis function."""
    
    @pytest.mark.asyncio
    async def test_connects_and_pings(self):
        """Should connect and ping Redis."""
        from app.services import redis_client
        
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock()
        
        with patch("app.services.redis_client.redis.from_url") as mock_from_url:
            mock_from_url.return_value = mock_client
            
            await redis_client.connect_redis()
        
        mock_client.ping.assert_called_once()


class TestCloseRedis:
    """Tests for close_redis function."""
    
    @pytest.mark.asyncio
    async def test_closes_connection(self):
        """Should close Redis connection."""
        from app.services import redis_client
        
        mock_client = AsyncMock()
        mock_client.close = AsyncMock()
        
        with patch.object(redis_client, "redis_client", mock_client):
            await redis_client.close_redis()
        
        mock_client.close.assert_called_once()
