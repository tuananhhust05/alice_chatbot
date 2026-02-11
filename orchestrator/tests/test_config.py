"""
Tests for config module - is_retryable_error function and settings.
"""
import pytest
from app.config import is_retryable_error, RETRYABLE_ERRORS, Settings


class TestIsRetryableError:
    """Tests for is_retryable_error function."""
    
    def test_timeout_error_is_retryable(self):
        error = Exception("Connection timeout occurred")
        assert is_retryable_error(error) == True
    
    def test_rate_limit_error_is_retryable(self):
        error = Exception("rate_limit exceeded, please try again")
        assert is_retryable_error(error) == True
    
    def test_connection_error_is_retryable(self):
        error = Exception("Connection refused to server")
        assert is_retryable_error(error) == True
    
    def test_network_error_is_retryable(self):
        error = Exception("Network unreachable")
        assert is_retryable_error(error) == True
    
    def test_503_error_is_retryable(self):
        error = Exception("HTTP 503 Service Unavailable")
        assert is_retryable_error(error) == True
    
    def test_504_error_is_retryable(self):
        error = Exception("504 Gateway Timeout")
        assert is_retryable_error(error) == True
    
    def test_429_error_is_retryable(self):
        error = Exception("429 Too Many Requests")
        assert is_retryable_error(error) == True
    
    def test_temporary_error_is_retryable(self):
        error = Exception("Temporary failure, retrying...")
        assert is_retryable_error(error) == True
    
    def test_unavailable_error_is_retryable(self):
        error = Exception("Service temporarily unavailable")
        assert is_retryable_error(error) == True
    
    def test_overloaded_error_is_retryable(self):
        error = Exception("Server is overloaded")
        assert is_retryable_error(error) == True
    
    def test_validation_error_not_retryable(self):
        error = Exception("Invalid input format")
        assert is_retryable_error(error) == False
    
    def test_auth_error_not_retryable(self):
        error = Exception("Authentication failed")
        assert is_retryable_error(error) == False
    
    def test_not_found_error_not_retryable(self):
        error = Exception("Resource not found")
        assert is_retryable_error(error) == False
    
    def test_permission_error_not_retryable(self):
        error = Exception("Permission denied")
        assert is_retryable_error(error) == False
    
    def test_case_insensitive(self):
        error = Exception("TIMEOUT ERROR")
        assert is_retryable_error(error) == True
    
    def test_empty_error_message(self):
        error = Exception("")
        assert is_retryable_error(error) == False


class TestRetryableErrors:
    """Tests for RETRYABLE_ERRORS constant."""
    
    def test_contains_timeout(self):
        assert "timeout" in RETRYABLE_ERRORS
    
    def test_contains_rate_limit(self):
        assert "rate_limit" in RETRYABLE_ERRORS
    
    def test_contains_connection(self):
        assert "connection" in RETRYABLE_ERRORS
    
    def test_contains_http_error_codes(self):
        assert "503" in RETRYABLE_ERRORS
        assert "504" in RETRYABLE_ERRORS
        assert "429" in RETRYABLE_ERRORS


class TestSettings:
    """Tests for Settings class."""
    
    def test_default_max_retry_count(self):
        settings = Settings()
        assert settings.MAX_RETRY_COUNT == 5
    
    def test_default_backoff_base(self):
        settings = Settings()
        assert settings.RETRY_BACKOFF_BASE == 1.0
    
    def test_default_backoff_multiplier(self):
        settings = Settings()
        assert settings.RETRY_BACKOFF_MULTIPLIER == 2.0
    
    def test_default_backoff_max(self):
        settings = Settings()
        assert settings.RETRY_BACKOFF_MAX == 120.0
    
    def test_default_jitter_max(self):
        settings = Settings()
        assert settings.RETRY_JITTER_MAX == 2.0
    
    def test_default_max_workers(self):
        settings = Settings()
        assert settings.MAX_WORKERS == 10
    
    def test_default_redis_ttl(self):
        settings = Settings()
        assert settings.REDIS_RESULT_TTL == 300
