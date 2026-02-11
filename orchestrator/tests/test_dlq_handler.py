"""
Tests for dlq_handler service (Dead Letter Queue).
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime
from bson import ObjectId

from app.services.dlq_handler import (
    save_to_dlq,
    get_dlq_items,
    get_dlq_item_detail,
    mark_dlq_retried,
    mark_dlq_resolved,
    delete_dlq_item,
    get_dlq_stats,
    DLQItem,
)


class TestDLQItemModel:
    """Tests for DLQItem Pydantic model."""
    
    def test_creates_valid_item(self):
        now = datetime.utcnow()
        item = DLQItem(
            id="123",
            request_id="req_456",
            original_topic="chat_requests",
            message_data={"message": "Hello"},
            error="Timeout",
            retry_count=5,
            first_failed_at=now,
            last_failed_at=now,
            status="pending",
        )
        
        assert item.id == "123"
        assert item.request_id == "req_456"
        assert item.status == "pending"
    
    def test_requires_all_fields(self):
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            DLQItem(id="123")  # Missing required fields


class TestSaveToDLQ:
    """Tests for save_to_dlq function."""
    
    @pytest.mark.asyncio
    async def test_creates_new_entry(self, mock_db):
        """Should create new DLQ entry when not exists."""
        mock_db.dead_letter_queue.find_one = AsyncMock(return_value=None)
        mock_db.dead_letter_queue.insert_one = AsyncMock(
            return_value=MagicMock(inserted_id=ObjectId())
        )
        
        with patch("app.services.dlq_handler.get_db", return_value=mock_db):
            result = await save_to_dlq(
                request_id="req_123",
                original_topic="chat_requests",
                message_data={"message": "Hello"},
                error="Rate limit exceeded",
                retry_count=5,
            )
        
        assert result is not None
        mock_db.dead_letter_queue.insert_one.assert_called_once()
        
        # Check the inserted document
        call_args = mock_db.dead_letter_queue.insert_one.call_args[0][0]
        assert call_args["request_id"] == "req_123"
        assert call_args["original_topic"] == "chat_requests"
        assert call_args["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_updates_existing_entry(self, mock_db, mock_dlq_item):
        """Should update existing entry (idempotency)."""
        mock_db.dead_letter_queue.find_one = AsyncMock(return_value=mock_dlq_item)
        mock_db.dead_letter_queue.update_one = AsyncMock()
        
        with patch("app.services.dlq_handler.get_db", return_value=mock_db):
            result = await save_to_dlq(
                request_id="req_123",
                original_topic="chat_requests",
                message_data={"message": "Hello"},
                error="New error",
                retry_count=6,
            )
        
        mock_db.dead_letter_queue.update_one.assert_called_once()
        mock_db.dead_letter_queue.insert_one.assert_not_called()


class TestGetDLQItems:
    """Tests for get_dlq_items function."""
    
    @pytest.mark.asyncio
    async def test_returns_items_list(self, mock_db, mock_dlq_item):
        """Should return list of DLQ items."""
        async def async_iter():
            yield mock_dlq_item
        
        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.__aiter__ = lambda self: async_iter()
        
        mock_db.dead_letter_queue.find = MagicMock(return_value=mock_cursor)
        
        with patch("app.services.dlq_handler.get_db", return_value=mock_db):
            items = await get_dlq_items()
        
        assert len(items) == 1
        assert items[0]["request_id"] == "req_123"
    
    @pytest.mark.asyncio
    async def test_filters_by_status(self, mock_db):
        """Should filter by status when provided."""
        async def async_iter():
            return
            yield
        
        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.__aiter__ = lambda self: async_iter()
        
        mock_db.dead_letter_queue.find = MagicMock(return_value=mock_cursor)
        
        with patch("app.services.dlq_handler.get_db", return_value=mock_db):
            await get_dlq_items(status="pending")
        
        # Check that find was called with status filter
        call_args = mock_db.dead_letter_queue.find.call_args[0][0]
        assert call_args["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_respects_limit_and_skip(self, mock_db):
        """Should apply limit and skip parameters."""
        async def async_iter():
            return
            yield
        
        mock_cursor = MagicMock()
        mock_cursor.sort = MagicMock(return_value=mock_cursor)
        mock_cursor.skip = MagicMock(return_value=mock_cursor)
        mock_cursor.limit = MagicMock(return_value=mock_cursor)
        mock_cursor.__aiter__ = lambda self: async_iter()
        
        mock_db.dead_letter_queue.find = MagicMock(return_value=mock_cursor)
        
        with patch("app.services.dlq_handler.get_db", return_value=mock_db):
            await get_dlq_items(limit=10, skip=5)
        
        mock_cursor.skip.assert_called_with(5)
        mock_cursor.limit.assert_called_with(10)


class TestGetDLQItemDetail:
    """Tests for get_dlq_item_detail function."""
    
    @pytest.mark.asyncio
    async def test_returns_item_detail(self, mock_db, mock_dlq_item):
        """Should return full item detail."""
        mock_db.dead_letter_queue.find_one = AsyncMock(return_value=mock_dlq_item)
        
        with patch("app.services.dlq_handler.get_db", return_value=mock_db):
            result = await get_dlq_item_detail(str(mock_dlq_item["_id"]))
        
        assert result is not None
        assert result["request_id"] == "req_123"
        assert "message_data" in result
    
    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, mock_db):
        """Should return None when item not found."""
        mock_db.dead_letter_queue.find_one = AsyncMock(return_value=None)
        
        with patch("app.services.dlq_handler.get_db", return_value=mock_db):
            result = await get_dlq_item_detail(str(ObjectId()))
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_handles_invalid_id(self, mock_db):
        """Should handle invalid ObjectId gracefully."""
        with patch("app.services.dlq_handler.get_db", return_value=mock_db):
            result = await get_dlq_item_detail("invalid_id")
        
        assert result is None


class TestMarkDLQRetried:
    """Tests for mark_dlq_retried function."""
    
    @pytest.mark.asyncio
    async def test_updates_status_to_retried(self, mock_db):
        """Should update status to 'retried'."""
        mock_db.dead_letter_queue.update_one = AsyncMock()
        dlq_id = str(ObjectId())
        
        with patch("app.services.dlq_handler.get_db", return_value=mock_db):
            await mark_dlq_retried(dlq_id)
        
        mock_db.dead_letter_queue.update_one.assert_called_once()
        call_args = mock_db.dead_letter_queue.update_one.call_args
        assert call_args[0][1]["$set"]["status"] == "retried"


class TestMarkDLQResolved:
    """Tests for mark_dlq_resolved function."""
    
    @pytest.mark.asyncio
    async def test_updates_status_to_resolved(self, mock_db):
        """Should update status to 'resolved'."""
        mock_db.dead_letter_queue.update_one = AsyncMock()
        dlq_id = str(ObjectId())
        
        with patch("app.services.dlq_handler.get_db", return_value=mock_db):
            await mark_dlq_resolved(dlq_id)
        
        mock_db.dead_letter_queue.update_one.assert_called_once()
        call_args = mock_db.dead_letter_queue.update_one.call_args
        assert call_args[0][1]["$set"]["status"] == "resolved"


class TestDeleteDLQItem:
    """Tests for delete_dlq_item function."""
    
    @pytest.mark.asyncio
    async def test_deletes_item(self, mock_db):
        """Should delete item and return True."""
        mock_db.dead_letter_queue.delete_one = AsyncMock(
            return_value=MagicMock(deleted_count=1)
        )
        dlq_id = str(ObjectId())
        
        with patch("app.services.dlq_handler.get_db", return_value=mock_db):
            result = await delete_dlq_item(dlq_id)
        
        assert result == True
    
    @pytest.mark.asyncio
    async def test_returns_false_when_not_found(self, mock_db):
        """Should return False when item not found."""
        mock_db.dead_letter_queue.delete_one = AsyncMock(
            return_value=MagicMock(deleted_count=0)
        )
        
        with patch("app.services.dlq_handler.get_db", return_value=mock_db):
            result = await delete_dlq_item(str(ObjectId()))
        
        assert result == False


class TestGetDLQStats:
    """Tests for get_dlq_stats function."""
    
    @pytest.mark.asyncio
    async def test_returns_status_counts(self, mock_db):
        """Should return counts by status."""
        async def status_iter():
            yield {"_id": "pending", "count": 10}
            yield {"_id": "retried", "count": 5}
            yield {"_id": "resolved", "count": 3}
        
        async def topic_iter():
            yield {"_id": "chat_requests", "count": 8}
            yield {"_id": "file_requests", "count": 2}
        
        mock_db.dead_letter_queue.aggregate = MagicMock(
            side_effect=[status_iter(), topic_iter()]
        )
        
        with patch("app.services.dlq_handler.get_db", return_value=mock_db):
            stats = await get_dlq_stats()
        
        assert stats["pending"] == 10
        assert stats["retried"] == 5
        assert stats["resolved"] == 3
        assert stats["total"] == 18
    
    @pytest.mark.asyncio
    async def test_includes_topic_breakdown(self, mock_db):
        """Should include breakdown by topic."""
        async def status_iter():
            return
            yield
        
        async def topic_iter():
            yield {"_id": "chat_requests", "count": 5}
        
        mock_db.dead_letter_queue.aggregate = MagicMock(
            side_effect=[status_iter(), topic_iter()]
        )
        
        with patch("app.services.dlq_handler.get_db", return_value=mock_db):
            stats = await get_dlq_stats()
        
        assert "by_topic" in stats
        assert stats["by_topic"]["chat_requests"] == 5
