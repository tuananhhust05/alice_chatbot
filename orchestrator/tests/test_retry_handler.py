"""
Tests for retry_handler service.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.services.retry_handler import (
    calculate_backoff_delay,
    should_retry,
    create_retry_payload,
    extract_retry_info,
    wait_for_backoff,
)


class TestCalculateBackoffDelay:
    """Tests for calculate_backoff_delay function."""
    
    def test_first_retry_delay(self):
        """First retry should be ~2s + jitter."""
        with patch("app.services.retry_handler.settings") as mock_settings:
            mock_settings.RETRY_BACKOFF_BASE = 1.0
            mock_settings.RETRY_BACKOFF_MULTIPLIER = 2.0
            mock_settings.RETRY_BACKOFF_MAX = 120.0
            mock_settings.RETRY_JITTER_MAX = 0.0  # No jitter for predictable test
            
            delay = calculate_backoff_delay(1)
        
        assert delay == 2.0  # 1 * 2^1 = 2
    
    def test_second_retry_delay(self):
        """Second retry should be ~4s + jitter."""
        with patch("app.services.retry_handler.settings") as mock_settings:
            mock_settings.RETRY_BACKOFF_BASE = 1.0
            mock_settings.RETRY_BACKOFF_MULTIPLIER = 2.0
            mock_settings.RETRY_BACKOFF_MAX = 120.0
            mock_settings.RETRY_JITTER_MAX = 0.0
            
            delay = calculate_backoff_delay(2)
        
        assert delay == 4.0  # 1 * 2^2 = 4
    
    def test_third_retry_delay(self):
        """Third retry should be ~8s + jitter."""
        with patch("app.services.retry_handler.settings") as mock_settings:
            mock_settings.RETRY_BACKOFF_BASE = 1.0
            mock_settings.RETRY_BACKOFF_MULTIPLIER = 2.0
            mock_settings.RETRY_BACKOFF_MAX = 120.0
            mock_settings.RETRY_JITTER_MAX = 0.0
            
            delay = calculate_backoff_delay(3)
        
        assert delay == 8.0  # 1 * 2^3 = 8
    
    def test_respects_max_backoff(self):
        """Delay should not exceed max backoff."""
        with patch("app.services.retry_handler.settings") as mock_settings:
            mock_settings.RETRY_BACKOFF_BASE = 1.0
            mock_settings.RETRY_BACKOFF_MULTIPLIER = 2.0
            mock_settings.RETRY_BACKOFF_MAX = 30.0
            mock_settings.RETRY_JITTER_MAX = 0.0
            
            # 2^10 = 1024, but max is 30
            delay = calculate_backoff_delay(10)
        
        assert delay == 30.0
    
    def test_adds_jitter(self):
        """Delay should include random jitter."""
        with patch("app.services.retry_handler.settings") as mock_settings:
            mock_settings.RETRY_BACKOFF_BASE = 1.0
            mock_settings.RETRY_BACKOFF_MULTIPLIER = 2.0
            mock_settings.RETRY_BACKOFF_MAX = 120.0
            mock_settings.RETRY_JITTER_MAX = 2.0
            
            delay = calculate_backoff_delay(1)
        
        # Should be between 2 and 4 (base 2 + jitter 0-2)
        assert 2.0 <= delay <= 4.0
    
    def test_zero_retry_count(self):
        """Zero retry count should use base delay."""
        with patch("app.services.retry_handler.settings") as mock_settings:
            mock_settings.RETRY_BACKOFF_BASE = 1.0
            mock_settings.RETRY_BACKOFF_MULTIPLIER = 2.0
            mock_settings.RETRY_BACKOFF_MAX = 120.0
            mock_settings.RETRY_JITTER_MAX = 0.0
            
            delay = calculate_backoff_delay(0)
        
        assert delay == 1.0  # 1 * 2^0 = 1


class TestShouldRetry:
    """Tests for should_retry function."""
    
    def test_retries_timeout_error(self):
        """Timeout errors should be retried."""
        with patch("app.services.retry_handler.settings") as mock_settings:
            mock_settings.MAX_RETRY_COUNT = 5
            
            error = Exception("Connection timeout")
            result = should_retry(error, retry_count=2)
        
        assert result == True
    
    def test_retries_rate_limit_error(self):
        """Rate limit errors should be retried."""
        with patch("app.services.retry_handler.settings") as mock_settings:
            mock_settings.MAX_RETRY_COUNT = 5
            
            error = Exception("429 rate_limit exceeded")
            result = should_retry(error, retry_count=1)
        
        assert result == True
    
    def test_does_not_retry_validation_error(self):
        """Validation errors should not be retried."""
        with patch("app.services.retry_handler.settings") as mock_settings:
            mock_settings.MAX_RETRY_COUNT = 5
            
            error = Exception("Invalid input format")
            result = should_retry(error, retry_count=0)
        
        assert result == False
    
    def test_does_not_retry_when_max_reached(self):
        """Should not retry when max count reached."""
        with patch("app.services.retry_handler.settings") as mock_settings:
            mock_settings.MAX_RETRY_COUNT = 5
            
            error = Exception("Connection timeout")
            result = should_retry(error, retry_count=5)
        
        assert result == False
    
    def test_does_not_retry_when_over_max(self):
        """Should not retry when over max count."""
        with patch("app.services.retry_handler.settings") as mock_settings:
            mock_settings.MAX_RETRY_COUNT = 5
            
            error = Exception("Connection timeout")
            result = should_retry(error, retry_count=10)
        
        assert result == False


class TestCreateRetryPayload:
    """Tests for create_retry_payload function."""
    
    def test_includes_original_data(self):
        """Payload should include original message data."""
        with patch("app.services.retry_handler.settings") as mock_settings:
            mock_settings.MAX_RETRY_COUNT = 5
            mock_settings.RETRY_BACKOFF_BASE = 1.0
            mock_settings.RETRY_BACKOFF_MULTIPLIER = 2.0
            mock_settings.RETRY_BACKOFF_MAX = 120.0
            mock_settings.RETRY_JITTER_MAX = 0.0
            
            original = {"message": "Hello", "user_id": "test@example.com"}
            payload = create_retry_payload(original, "chat_requests", "timeout", 0)
        
        assert payload["message"] == "Hello"
        assert payload["user_id"] == "test@example.com"
    
    def test_includes_retry_metadata(self):
        """Payload should include _retry metadata."""
        with patch("app.services.retry_handler.settings") as mock_settings:
            mock_settings.MAX_RETRY_COUNT = 5
            mock_settings.RETRY_BACKOFF_BASE = 1.0
            mock_settings.RETRY_BACKOFF_MULTIPLIER = 2.0
            mock_settings.RETRY_BACKOFF_MAX = 120.0
            mock_settings.RETRY_JITTER_MAX = 0.0
            
            payload = create_retry_payload({}, "chat_requests", "timeout error", 0)
        
        assert "_retry" in payload
        assert payload["_retry"]["original_topic"] == "chat_requests"
        assert payload["_retry"]["retry_count"] == 1  # Incremented
        assert payload["_retry"]["max_retry"] == 5
        assert payload["_retry"]["last_error"] == "timeout error"
    
    def test_increments_retry_count(self):
        """Retry count should be incremented."""
        with patch("app.services.retry_handler.settings") as mock_settings:
            mock_settings.MAX_RETRY_COUNT = 5
            mock_settings.RETRY_BACKOFF_BASE = 1.0
            mock_settings.RETRY_BACKOFF_MULTIPLIER = 2.0
            mock_settings.RETRY_BACKOFF_MAX = 120.0
            mock_settings.RETRY_JITTER_MAX = 0.0
            
            payload = create_retry_payload({}, "topic", "error", retry_count=3)
        
        assert payload["_retry"]["retry_count"] == 4
    
    def test_includes_timestamp(self):
        """Payload should include last_attempt timestamp."""
        with patch("app.services.retry_handler.settings") as mock_settings:
            mock_settings.MAX_RETRY_COUNT = 5
            mock_settings.RETRY_BACKOFF_BASE = 1.0
            mock_settings.RETRY_BACKOFF_MULTIPLIER = 2.0
            mock_settings.RETRY_BACKOFF_MAX = 120.0
            mock_settings.RETRY_JITTER_MAX = 0.0
            
            payload = create_retry_payload({}, "topic", "error", 0)
        
        assert "last_attempt" in payload["_retry"]
    
    def test_includes_next_delay(self):
        """Payload should include calculated next delay."""
        with patch("app.services.retry_handler.settings") as mock_settings:
            mock_settings.MAX_RETRY_COUNT = 5
            mock_settings.RETRY_BACKOFF_BASE = 1.0
            mock_settings.RETRY_BACKOFF_MULTIPLIER = 2.0
            mock_settings.RETRY_BACKOFF_MAX = 120.0
            mock_settings.RETRY_JITTER_MAX = 0.0
            
            payload = create_retry_payload({}, "topic", "error", retry_count=0)
        
        assert payload["_retry"]["next_delay"] == 2.0  # 1 * 2^1


class TestExtractRetryInfo:
    """Tests for extract_retry_info function."""
    
    def test_extracts_retry_info(self):
        """Should extract _retry field from data."""
        data = {
            "message": "Hello",
            "_retry": {
                "original_topic": "chat_requests",
                "retry_count": 2,
            }
        }
        
        original, retry_info = extract_retry_info(data)
        
        assert retry_info is not None
        assert retry_info["original_topic"] == "chat_requests"
        assert retry_info["retry_count"] == 2
    
    def test_removes_retry_from_data(self):
        """Should remove _retry from original data."""
        data = {
            "message": "Hello",
            "_retry": {"retry_count": 1}
        }
        
        original, _ = extract_retry_info(data)
        
        assert "_retry" not in original
        assert original["message"] == "Hello"
    
    def test_returns_none_when_no_retry(self):
        """Should return None when no _retry field."""
        data = {"message": "Hello"}
        
        original, retry_info = extract_retry_info(data)
        
        assert retry_info is None
        assert original["message"] == "Hello"


class TestWaitForBackoff:
    """Tests for wait_for_backoff async function."""
    
    @pytest.mark.asyncio
    async def test_waits_for_calculated_delay(self):
        """Should wait for calculated backoff delay."""
        with patch("app.services.retry_handler.settings") as mock_settings:
            mock_settings.RETRY_BACKOFF_BASE = 0.01  # Very short for testing
            mock_settings.RETRY_BACKOFF_MULTIPLIER = 2.0
            mock_settings.RETRY_BACKOFF_MAX = 1.0
            mock_settings.RETRY_JITTER_MAX = 0.0
            
            with patch("asyncio.sleep") as mock_sleep:
                mock_sleep.return_value = None
                
                await wait_for_backoff(1)
        
        mock_sleep.assert_called_once()
        # Delay should be approximately 0.02 (0.01 * 2^1)
        call_arg = mock_sleep.call_args[0][0]
        assert 0.01 <= call_arg <= 0.03
