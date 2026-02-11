"""
Tests for chat routes.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime
from bson import ObjectId


class TestSendMessageEndpoint:
    """Tests for POST /api/chat/send endpoint."""
    
    @pytest.mark.asyncio
    async def test_creates_new_conversation(self, authed_async_client):
        with patch("app.routes.chat.get_db") as mock_get_db, \
             patch("app.routes.chat.track_ip_access", new_callable=AsyncMock), \
             patch("app.routes.chat.publish_chat_request", new_callable=AsyncMock) as mock_kafka:
            mock_db = MagicMock()
            conv_id = ObjectId()
            
            # Mock insert
            mock_db.conversations.insert_one = AsyncMock(
                return_value=MagicMock(inserted_id=conv_id)
            )
            # Mock update
            mock_db.conversations.update_one = AsyncMock()
            # Mock ip_messages collection
            mock_db.ip_messages.insert_one = AsyncMock()
            
            mock_get_db.return_value = mock_db
            
            response = await authed_async_client.post(
                "/api/chat/send",
                json={"message": "Hello, AI!"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        assert "conversation_id" in data
    
    @pytest.mark.asyncio
    async def test_uses_display_content_for_title(self, authed_async_client):
        with patch("app.routes.chat.get_db") as mock_get_db, \
             patch("app.routes.chat.track_ip_access", new_callable=AsyncMock), \
             patch("app.routes.chat.publish_chat_request", new_callable=AsyncMock):
            mock_db = MagicMock()
            conv_id = ObjectId()
            
            mock_db.conversations.insert_one = AsyncMock(
                return_value=MagicMock(inserted_id=conv_id)
            )
            mock_db.conversations.update_one = AsyncMock()
            mock_db.ip_messages.insert_one = AsyncMock()
            
            mock_get_db.return_value = mock_db
            
            response = await authed_async_client.post(
                "/api/chat/send",
                json={
                    "message": "Long message with file content...",
                    "display_content": "[Attached: report.pdf]\n\nAnalyze this",
                }
            )
        
        assert response.status_code == 200
        
        # Check that insert was called with display_content in title
        insert_call = mock_db.conversations.insert_one.call_args
        inserted_doc = insert_call[0][0]
        assert "Attached" in inserted_doc["title"] or "Analyze" in inserted_doc["title"]
    
    @pytest.mark.asyncio
    async def test_appends_to_existing_conversation(self, authed_async_client, mock_user):
        conv_id = ObjectId()
        existing_conv = {
            "_id": conv_id,
            "user_id": mock_user["email"],
            "title": "Existing Chat",
            "messages": [],
            "file_ids": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        
        with patch("app.routes.chat.get_db") as mock_get_db, \
             patch("app.routes.chat.track_ip_access", new_callable=AsyncMock), \
             patch("app.routes.chat.publish_chat_request", new_callable=AsyncMock):
            mock_db = MagicMock()
            mock_db.conversations.find_one = AsyncMock(return_value=existing_conv)
            mock_db.conversations.update_one = AsyncMock()
            mock_db.ip_messages.insert_one = AsyncMock()
            
            mock_get_db.return_value = mock_db
            
            response = await authed_async_client.post(
                "/api/chat/send",
                json={
                    "message": "Follow up message",
                    "conversation_id": str(conv_id),
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == str(conv_id)
    
    @pytest.mark.asyncio
    async def test_returns_404_for_nonexistent_conversation(self, authed_async_client):
        fake_conv_id = str(ObjectId())
        
        with patch("app.routes.chat.get_db") as mock_get_db, \
             patch("app.routes.chat.publish_chat_request", new_callable=AsyncMock):
            mock_db = MagicMock()
            mock_db.conversations.find_one = AsyncMock(return_value=None)
            
            mock_get_db.return_value = mock_db
            
            response = await authed_async_client.post(
                "/api/chat/send",
                json={
                    "message": "Message to nonexistent",
                    "conversation_id": fake_conv_id,
                }
            )
        
        assert response.status_code == 404


class TestListConversationsEndpoint:
    """Tests for GET /api/chat/conversations endpoint."""
    
    @pytest.mark.asyncio
    async def test_returns_conversations_list(self, authed_async_client, mock_user):
        now = datetime.utcnow()
        mock_convs = [
            {
                "_id": ObjectId(),
                "user_id": mock_user["email"],
                "title": "Chat 1",
                "messages": [{"role": "user", "content": "Hi"}],
                "file_ids": [],
                "created_at": now,
                "updated_at": now,
            },
            {
                "_id": ObjectId(),
                "user_id": mock_user["email"],
                "title": "Chat 2",
                "messages": [],
                "file_ids": [],
                "created_at": now,
                "updated_at": now,
            },
        ]
        
        with patch("app.routes.chat.get_db") as mock_get_db:
            mock_db = MagicMock()
            
            # Create async iterator for cursor
            async def async_iter():
                for conv in mock_convs:
                    yield conv
            
            mock_cursor = MagicMock()
            mock_cursor.sort = MagicMock(return_value=mock_cursor)
            mock_cursor.limit = MagicMock(return_value=mock_cursor)
            mock_cursor.__aiter__ = lambda self: async_iter()
            mock_db.conversations.find = MagicMock(return_value=mock_cursor)
            
            mock_get_db.return_value = mock_db
            
            response = await authed_async_client.get("/api/chat/conversations")
        
        assert response.status_code == 200
        data = response.json()
        # API returns list directly, not {"conversations": [...]}
        assert isinstance(data, list)
        assert len(data) == 2
    
    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_conversations(self, authed_async_client):
        with patch("app.routes.chat.get_db") as mock_get_db:
            mock_db = MagicMock()
            
            # Create async iterator for empty cursor
            async def async_iter():
                return
                yield  # Make it a generator
            
            mock_cursor = MagicMock()
            mock_cursor.sort = MagicMock(return_value=mock_cursor)
            mock_cursor.limit = MagicMock(return_value=mock_cursor)
            mock_cursor.__aiter__ = lambda self: async_iter()
            mock_db.conversations.find = MagicMock(return_value=mock_cursor)
            
            mock_get_db.return_value = mock_db
            
            response = await authed_async_client.get("/api/chat/conversations")
        
        assert response.status_code == 200
        data = response.json()
        assert data == []


class TestGetConversationEndpoint:
    """Tests for GET /api/chat/conversations/{id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_returns_conversation_detail(self, authed_async_client, mock_user):
        conv_id = ObjectId()
        now = datetime.utcnow()
        mock_conv = {
            "_id": conv_id,
            "user_id": mock_user["email"],
            "title": "Test Chat",
            "messages": [
                {"role": "user", "content": "Hello!", "timestamp": now},
                {"role": "assistant", "content": "Hi!", "timestamp": now},
            ],
            "file_ids": [],
            "created_at": now,
            "updated_at": now,
        }
        
        with patch("app.routes.chat.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_db.conversations.find_one = AsyncMock(return_value=mock_conv)
            mock_get_db.return_value = mock_db
            
            response = await authed_async_client.get(f"/api/chat/conversations/{conv_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Chat"
        assert len(data["messages"]) == 2
    
    @pytest.mark.asyncio
    async def test_returns_404_for_nonexistent(self, authed_async_client):
        with patch("app.routes.chat.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_db.conversations.find_one = AsyncMock(return_value=None)
            mock_get_db.return_value = mock_db
            
            response = await authed_async_client.get(f"/api/chat/conversations/{ObjectId()}")
        
        assert response.status_code == 404


class TestDeleteConversationEndpoint:
    """Tests for DELETE /api/chat/conversations/{id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_deletes_conversation(self, authed_async_client, mock_user):
        conv_id = ObjectId()
        
        with patch("app.routes.chat.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_db.conversations.delete_one = AsyncMock(
                return_value=MagicMock(deleted_count=1)
            )
            mock_get_db.return_value = mock_db
            
            response = await authed_async_client.delete(f"/api/chat/conversations/{conv_id}")
        
        assert response.status_code == 200
        assert response.json()["message"] == "Conversation deleted"
    
    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self, authed_async_client):
        with patch("app.routes.chat.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_db.conversations.delete_one = AsyncMock(
                return_value=MagicMock(deleted_count=0)
            )
            mock_get_db.return_value = mock_db
            
            response = await authed_async_client.delete(f"/api/chat/conversations/{ObjectId()}")
        
        assert response.status_code == 404
