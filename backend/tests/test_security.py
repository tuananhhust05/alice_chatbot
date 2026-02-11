"""
Tests for backend security module.
"""
import pytest
import time
from unittest.mock import MagicMock, patch

from app.security import (
    check_rate_limit,
    validate_input,
    validate_filename,
    validate_json_content,
    get_client_ip,
    RATE_LIMIT_WINDOW,
    RATE_LIMIT_MAX_REQUESTS,
)


class TestCheckRateLimit:
    """Tests for check_rate_limit function."""
    
    def test_allows_first_request(self):
        """First request should be allowed."""
        # Use unique key to avoid test interference
        key = f"test_first_{time.time()}"
        result = check_rate_limit(key, max_requests=10)
        
        assert result == True
    
    def test_allows_requests_under_limit(self):
        """Requests under limit should be allowed."""
        key = f"test_under_{time.time()}"
        
        for i in range(5):
            result = check_rate_limit(key, max_requests=10)
            assert result == True
    
    def test_blocks_requests_over_limit(self):
        """Requests over limit should be blocked."""
        key = f"test_over_{time.time()}"
        
        # Make requests up to limit
        for i in range(5):
            check_rate_limit(key, max_requests=5)
        
        # Next request should be blocked
        result = check_rate_limit(key, max_requests=5)
        assert result == False
    
    def test_different_keys_independent(self):
        """Different keys should have independent limits."""
        key1 = f"test_key1_{time.time()}"
        key2 = f"test_key2_{time.time()}"
        
        # Max out key1
        for i in range(5):
            check_rate_limit(key1, max_requests=5)
        
        # key2 should still work
        result = check_rate_limit(key2, max_requests=5)
        assert result == True


class TestValidateInput:
    """Tests for validate_input function."""
    
    def test_valid_normal_text(self):
        """Normal text should be valid."""
        is_valid, error = validate_input("Hello, how are you?")
        
        assert is_valid == True
        assert error is None
    
    def test_rejects_too_long_input(self):
        """Too long input should be rejected."""
        long_text = "A" * 60000
        is_valid, error = validate_input(long_text, max_length=50000)
        
        assert is_valid == False
        assert "too long" in error.lower()
    
    def test_rejects_script_tags(self):
        """Script tags should be rejected."""
        text = "Hello <script>alert('xss')</script>"
        is_valid, error = validate_input(text)
        
        assert is_valid == False
        assert "dangerous" in error.lower()
    
    def test_rejects_javascript_urls(self):
        """JavaScript URLs should be rejected."""
        text = "Click here: javascript:alert('xss')"
        is_valid, error = validate_input(text)
        
        assert is_valid == False
    
    def test_rejects_event_handlers(self):
        """Event handlers should be rejected."""
        text = '<img onerror="alert(1)">'
        is_valid, error = validate_input(text)
        
        assert is_valid == False
    
    def test_empty_is_valid(self):
        """Empty string should be valid."""
        is_valid, error = validate_input("")
        
        assert is_valid == True


class TestValidateFilename:
    """Tests for validate_filename function."""
    
    def test_valid_filename(self):
        """Normal filename should be valid."""
        is_valid, error = validate_filename("document.pdf")
        
        assert is_valid == True
        assert error is None
    
    def test_rejects_empty_filename(self):
        """Empty filename should be rejected."""
        is_valid, error = validate_filename("")
        
        assert is_valid == False
    
    def test_rejects_path_traversal(self):
        """Path traversal should be rejected."""
        is_valid, error = validate_filename("../../../etc/passwd")
        
        assert is_valid == False
        assert "Invalid" in error
    
    def test_rejects_forward_slash(self):
        """Forward slash should be rejected."""
        is_valid, error = validate_filename("path/to/file.txt")
        
        assert is_valid == False
    
    def test_rejects_backslash(self):
        """Backslash should be rejected."""
        is_valid, error = validate_filename("path\\to\\file.txt")
        
        assert is_valid == False
    
    def test_rejects_null_bytes(self):
        """Null bytes should be rejected."""
        is_valid, error = validate_filename("file\x00.txt")
        
        assert is_valid == False
    
    def test_rejects_too_long_filename(self):
        """Too long filename should be rejected."""
        is_valid, error = validate_filename("A" * 300)
        
        assert is_valid == False
        assert "too long" in error.lower()


class TestValidateJsonContent:
    """Tests for validate_json_content function."""
    
    def test_valid_shallow_json(self):
        """Shallow JSON should be valid."""
        data = {"key": "value", "number": 123}
        result = validate_json_content(data)
        
        assert result == True
    
    def test_valid_nested_json(self):
        """Reasonably nested JSON should be valid."""
        data = {"level1": {"level2": {"level3": "value"}}}
        result = validate_json_content(data)
        
        assert result == True
    
    def test_rejects_deeply_nested_json(self):
        """Deeply nested JSON should be rejected."""
        # Build deeply nested structure
        data = {"value": "deep"}
        for i in range(15):
            data = {"nested": data}
        
        result = validate_json_content(data, max_depth=10)
        
        assert result == False
    
    def test_handles_arrays(self):
        """Arrays should be validated."""
        data = {"items": [{"nested": {"value": 1}}]}
        result = validate_json_content(data)
        
        assert result == True


class TestGetClientIp:
    """Tests for get_client_ip function."""
    
    def test_extracts_from_forwarded_header(self):
        """Should extract IP from X-Forwarded-For header."""
        request = MagicMock()
        request.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}
        request.client.host = "127.0.0.1"
        
        ip = get_client_ip(request)
        
        assert ip == "192.168.1.1"
    
    def test_falls_back_to_client_host(self):
        """Should fall back to client host if no header."""
        request = MagicMock()
        request.headers = {}
        request.client.host = "192.168.1.100"
        
        ip = get_client_ip(request)
        
        assert ip == "192.168.1.100"
    
    def test_handles_missing_client(self):
        """Should handle missing client."""
        request = MagicMock()
        request.headers = {}
        request.client = None
        
        ip = get_client_ip(request)
        
        assert ip == "unknown"
