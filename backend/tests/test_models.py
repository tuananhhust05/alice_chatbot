"""
Tests for chat models (Pydantic validation).
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.chat import (
    Message,
    ChatRequest,
    ChatSendResponse,
    StreamResponse,
    ConversationListItem,
    ConversationDetail,
)


class TestMessage:
    """Tests for Message model."""
    
    def test_creates_valid_message(self):
        msg = Message(role="user", content="Hello")
        
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.timestamp is not None
    
    def test_accepts_user_role(self):
        msg = Message(role="user", content="Test")
        assert msg.role == "user"
    
    def test_accepts_assistant_role(self):
        msg = Message(role="assistant", content="Test")
        assert msg.role == "assistant"
    
    def test_requires_role(self):
        with pytest.raises(ValidationError):
            Message(content="Hello")
    
    def test_requires_content(self):
        with pytest.raises(ValidationError):
            Message(role="user")
    
    def test_accepts_custom_timestamp(self):
        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        msg = Message(role="user", content="Test", timestamp=custom_time)
        
        assert msg.timestamp == custom_time
    
    def test_default_timestamp_is_now(self):
        before = datetime.utcnow()
        msg = Message(role="user", content="Test")
        after = datetime.utcnow()
        
        assert before <= msg.timestamp <= after


class TestChatRequest:
    """Tests for ChatRequest model."""
    
    def test_creates_with_message_only(self):
        req = ChatRequest(message="Hello")
        
        assert req.message == "Hello"
        assert req.display_content is None
        assert req.conversation_id is None
    
    def test_accepts_all_fields(self):
        req = ChatRequest(
            message="Full message with file",
            display_content="[Attached: file.pdf]\n\nShort message",
            conversation_id="conv_123",
        )
        
        assert req.message == "Full message with file"
        assert req.display_content == "[Attached: file.pdf]\n\nShort message"
        assert req.conversation_id == "conv_123"
    
    def test_requires_message(self):
        with pytest.raises(ValidationError):
            ChatRequest()
    
    def test_allows_empty_message(self):
        # Empty string is valid (validation at route level)
        req = ChatRequest(message="")
        assert req.message == ""


class TestChatSendResponse:
    """Tests for ChatSendResponse model."""
    
    def test_creates_valid_response(self):
        resp = ChatSendResponse(request_id="req_123", conversation_id="conv_456")
        
        assert resp.request_id == "req_123"
        assert resp.conversation_id == "conv_456"
    
    def test_requires_both_fields(self):
        with pytest.raises(ValidationError):
            ChatSendResponse(request_id="req_123")
        
        with pytest.raises(ValidationError):
            ChatSendResponse(conversation_id="conv_456")


class TestStreamResponse:
    """Tests for StreamResponse model."""
    
    def test_creates_processing_response(self):
        resp = StreamResponse(status="processing")
        
        assert resp.status == "processing"
        assert resp.reply is None
        assert resp.finished == 0
    
    def test_creates_completed_response(self):
        resp = StreamResponse(
            status="completed",
            reply="AI response here",
            title="Chat Title",
            finished=1,
        )
        
        assert resp.status == "completed"
        assert resp.reply == "AI response here"
        assert resp.title == "Chat Title"
        assert resp.finished == 1
    
    def test_creates_error_response(self):
        resp = StreamResponse(
            status="error",
            error="Something went wrong",
            finished=1,
        )
        
        assert resp.status == "error"
        assert resp.error == "Something went wrong"
    
    def test_default_finished_is_zero(self):
        resp = StreamResponse(status="streaming")
        assert resp.finished == 0


class TestConversationListItem:
    """Tests for ConversationListItem model."""
    
    def test_creates_valid_item(self):
        now = datetime.utcnow()
        item = ConversationListItem(
            id="conv_123",
            title="My Chat",
            created_at=now,
            updated_at=now,
            message_count=5,
        )
        
        assert item.id == "conv_123"
        assert item.title == "My Chat"
        assert item.message_count == 5
    
    def test_default_message_count(self):
        now = datetime.utcnow()
        item = ConversationListItem(
            id="conv_123",
            title="Chat",
            created_at=now,
            updated_at=now,
        )
        
        assert item.message_count == 0


class TestConversationDetail:
    """Tests for ConversationDetail model."""
    
    def test_creates_with_messages(self):
        now = datetime.utcnow()
        messages = [
            Message(role="user", content="Hello"),
            Message(role="assistant", content="Hi!"),
        ]
        
        detail = ConversationDetail(
            id="conv_123",
            title="Chat",
            messages=messages,
            created_at=now,
            updated_at=now,
        )
        
        assert len(detail.messages) == 2
        assert detail.messages[0].role == "user"
    
    def test_default_empty_file_ids(self):
        now = datetime.utcnow()
        detail = ConversationDetail(
            id="conv_123",
            title="Chat",
            messages=[],
            created_at=now,
            updated_at=now,
        )
        
        assert detail.file_ids == []
    
    def test_accepts_file_ids(self):
        now = datetime.utcnow()
        detail = ConversationDetail(
            id="conv_123",
            title="Chat",
            messages=[],
            file_ids=["file_1", "file_2"],
            created_at=now,
            updated_at=now,
        )
        
        assert len(detail.file_ids) == 2
