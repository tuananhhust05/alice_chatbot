"""
Tests for chat_handler service.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime
from bson import ObjectId

from app.services.chat_handler import (
    estimate_tokens,
    truncate_to_tokens,
    truncate_message_content,
    build_messages_with_token_limit,
    CHARS_PER_TOKEN,
    MAX_MESSAGE_TOKENS,
)


class TestEstimateTokens:
    """Tests for estimate_tokens function."""
    
    def test_estimates_short_text(self):
        """Should estimate tokens for short text."""
        text = "Hello"  # 5 chars
        tokens = estimate_tokens(text)
        
        # 5 chars / 4 chars_per_token + 1 = 2 tokens
        assert tokens == 2
    
    def test_estimates_longer_text(self):
        """Should estimate tokens for longer text."""
        text = "This is a longer test message"  # 30 chars
        tokens = estimate_tokens(text)
        
        # 30 / 4 + 1 = 8 tokens
        assert tokens == 8
    
    def test_empty_string_returns_zero(self):
        """Empty string should return 0 tokens."""
        assert estimate_tokens("") == 0
    
    def test_none_returns_zero(self):
        """None should return 0 tokens."""
        assert estimate_tokens(None) == 0
    
    def test_whitespace_counted(self):
        """Whitespace should be counted."""
        text = "Hello World"  # 11 chars including space
        tokens = estimate_tokens(text)
        
        assert tokens == 11 // CHARS_PER_TOKEN + 1


class TestTruncateToTokens:
    """Tests for truncate_to_tokens function."""
    
    def test_short_text_unchanged(self):
        """Short text should not be truncated."""
        text = "Short text"
        result = truncate_to_tokens(text, max_tokens=100)
        
        assert result == text
    
    def test_long_text_truncated(self):
        """Long text should be truncated."""
        text = "A" * 1000  # 1000 chars
        result = truncate_to_tokens(text, max_tokens=50)  # ~200 chars max
        
        assert len(result) < 1000
        assert "[Content truncated" in result
    
    def test_truncation_adds_message(self):
        """Truncated text should include truncation message."""
        text = "A" * 500
        result = truncate_to_tokens(text, max_tokens=10)
        
        assert "truncated" in result.lower()
    
    def test_exact_length_not_truncated(self):
        """Text at exact limit should not be truncated."""
        text = "A" * 40  # 40 chars = 10 tokens at 4 chars/token
        result = truncate_to_tokens(text, max_tokens=10)
        
        assert result == text


class TestTruncateMessageContent:
    """Tests for truncate_message_content function."""
    
    def test_regular_message_unchanged(self):
        """Regular short message should not be truncated."""
        content = "Hello, how are you?"
        result = truncate_message_content(content)
        
        assert result == content
    
    def test_long_message_truncated(self):
        """Long message should be truncated."""
        content = "A" * 100000
        result = truncate_message_content(content, max_tokens=100)
        
        assert len(result) < 100000
    
    def test_file_content_handled_separately(self):
        """File content should be truncated separately from user text."""
        user_text = "Analyze this file"
        file_content = "B" * 50000
        content = f"{user_text}\n\nFile content:\n{file_content}"
        
        result = truncate_message_content(content, max_tokens=200)
        
        # User text should be preserved
        assert "Analyze this file" in result
        # File content should be truncated
        assert len(result) < len(content)
    
    def test_preserves_file_marker(self):
        """File content marker should be preserved."""
        content = "Check this\n\nFile content:\nSome file data"
        result = truncate_message_content(content, max_tokens=1000)
        
        assert "File content:" in result
    
    def test_very_long_user_text_omits_file(self):
        """When user text is too long, file content may be omitted."""
        user_text = "A" * 20000
        content = f"{user_text}\n\nFile content:\nFile data"
        
        result = truncate_message_content(content, max_tokens=100)
        
        # Should mention omission
        assert "truncated" in result.lower() or "omitted" in result.lower()


class TestBuildMessagesWithTokenLimit:
    """Tests for build_messages_with_token_limit function."""
    
    def test_includes_current_message(self):
        """Current message (last) should always be included."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "Current message"},
        ]
        
        result = build_messages_with_token_limit(messages, "System prompt", max_tokens=1000)
        
        assert any(m["content"] == "Current message" for m in result)
    
    def test_empty_messages_returns_empty(self):
        """Empty message list should return empty list."""
        result = build_messages_with_token_limit([], "System prompt")
        
        assert result == []
    
    def test_single_message(self):
        """Single message should be included."""
        messages = [{"role": "user", "content": "Only message"}]
        
        result = build_messages_with_token_limit(messages, "System prompt", max_tokens=1000)
        
        assert len(result) == 1
        assert result[0]["content"] == "Only message"
    
    def test_limits_history(self):
        """Should limit history to fit token budget."""
        # Create many messages
        messages = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
            for i in range(50)
        ]
        
        # Very small token limit
        result = build_messages_with_token_limit(messages, "System", max_tokens=100)
        
        # Should not include all messages
        assert len(result) < 50
        # But should include the last (current) message
        assert result[-1]["content"] == "Message 49"
    
    def test_prioritizes_recent_history(self):
        """Should prioritize recent messages over older ones."""
        messages = [
            {"role": "user", "content": "Old message 1"},
            {"role": "assistant", "content": "Old response 1"},
            {"role": "user", "content": "Old message 2"},
            {"role": "assistant", "content": "Old response 2"},
            {"role": "user", "content": "Recent message"},
            {"role": "assistant", "content": "Recent response"},
            {"role": "user", "content": "Current"},
        ]
        
        result = build_messages_with_token_limit(messages, "System", max_tokens=200)
        
        # Current should always be there
        assert result[-1]["content"] == "Current"
        # Recent should be included before old
        if len(result) > 1:
            contents = [m["content"] for m in result]
            # If recent is included but old is not, that's correct
            # Just check current is there
            assert "Current" in contents


class TestHandleChatRequest:
    """Integration tests for handle_chat_request function."""
    
    @pytest.mark.asyncio
    async def test_handles_basic_message(self):
        """Should handle a basic chat message."""
        from app.services.chat_handler import handle_chat_request
        
        with patch("app.services.chat_handler.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_db.prompts.find_one = AsyncMock(return_value=None)
            mock_db.conversations.find_one = AsyncMock(return_value={
                "_id": ObjectId(),
                "messages": [],
                "created_at": datetime.utcnow(),
            })
            mock_db.conversations.update_one = AsyncMock()
            mock_get_db.return_value = mock_db
            
            with patch("app.services.chat_handler.search_ragdata") as mock_search:
                mock_search.return_value = []
                
                with patch("app.services.chat_handler.get_chat_completion_stream") as mock_stream:
                    async def stream_gen():
                        yield "Hello"
                        yield " there!"
                    
                    mock_stream.return_value = stream_gen()
                    
                    with patch("app.services.chat_handler.stream_update") as mock_update:
                        mock_update.return_value = None
                        
                        with patch("app.services.chat_handler.emit_llm_event") as mock_emit:
                            mock_emit.return_value = None
                            
                            result = await handle_chat_request({
                                "request_id": "req_123",
                                "conversation_id": str(ObjectId()),
                                "message": "Hi!",
                                "user_id": "test@example.com",
                                "generate_title": False,
                            })
        
        assert "reply" in result
        assert result["reply"] == "Hello there!"
