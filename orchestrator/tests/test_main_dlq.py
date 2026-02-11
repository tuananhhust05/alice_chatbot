"""
Tests for main.py DLQ API endpoints.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime
from bson import ObjectId


class TestDLQStatsEndpoint:
    """Tests for GET /api/dlq/stats endpoint."""
    
    @pytest.mark.asyncio
    async def test_returns_stats(self, async_client):
        """Should return DLQ statistics."""
        with patch("app.main.get_dlq_stats") as mock_stats:
            mock_stats.return_value = {
                "pending": 10,
                "retried": 5,
                "resolved": 3,
                "total": 18,
                "by_topic": {"chat_requests": 8},
            }
            
            response = await async_client.get("/api/dlq/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["pending"] == 10
        assert data["total"] == 18
        assert "retry_config" in data


class TestDLQListEndpoint:
    """Tests for GET /api/dlq/items endpoint."""
    
    @pytest.mark.asyncio
    async def test_returns_items_list(self, async_client):
        """Should return list of DLQ items."""
        with patch("app.main.get_dlq_items") as mock_items:
            mock_items.return_value = [
                {
                    "id": "123",
                    "request_id": "req_123",
                    "original_topic": "chat_requests",
                    "last_error": "Timeout",
                    "retry_count": 5,
                    "first_failed_at": datetime.utcnow().isoformat(),
                    "last_failed_at": datetime.utcnow().isoformat(),
                    "status": "pending",
                    "error_count": 5,
                }
            ]
            
            response = await async_client.get("/api/dlq/items")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 1
    
    @pytest.mark.asyncio
    async def test_filters_by_status(self, async_client):
        """Should filter by status parameter."""
        with patch("app.main.get_dlq_items") as mock_items:
            mock_items.return_value = []
            
            await async_client.get("/api/dlq/items?status=pending")
        
        mock_items.assert_called_with(status="pending", limit=50, skip=0)
    
    @pytest.mark.asyncio
    async def test_respects_pagination(self, async_client):
        """Should respect limit and skip parameters."""
        with patch("app.main.get_dlq_items") as mock_items:
            mock_items.return_value = []
            
            await async_client.get("/api/dlq/items?limit=10&skip=20")
        
        mock_items.assert_called_with(status=None, limit=10, skip=20)


class TestDLQItemDetailEndpoint:
    """Tests for GET /api/dlq/items/{id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_returns_item_detail(self, async_client):
        """Should return full item detail."""
        dlq_id = str(ObjectId())
        
        with patch("app.main.get_dlq_item_detail") as mock_detail:
            mock_detail.return_value = {
                "id": dlq_id,
                "request_id": "req_123",
                "original_topic": "chat_requests",
                "message_data": {"message": "Hello"},
                "last_error": "Timeout",
                "retry_count": 5,
                "error_history": [],
                "first_failed_at": datetime.utcnow().isoformat(),
                "last_failed_at": datetime.utcnow().isoformat(),
                "status": "pending",
            }
            
            response = await async_client.get(f"/api/dlq/items/{dlq_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "message_data" in data
    
    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self, async_client):
        """Should return 404 when item not found."""
        with patch("app.main.get_dlq_item_detail") as mock_detail:
            mock_detail.return_value = None
            
            response = await async_client.get(f"/api/dlq/items/{ObjectId()}")
        
        assert response.status_code == 404


class TestDLQRetryEndpoint:
    """Tests for POST /api/dlq/items/{id}/retry endpoint."""
    
    @pytest.mark.asyncio
    async def test_retries_item(self, async_client):
        """Should retry DLQ item."""
        dlq_id = str(ObjectId())
        
        with patch("app.main.get_dlq_item_detail") as mock_detail:
            mock_detail.return_value = {
                "id": dlq_id,
                "request_id": "req_123",
                "original_topic": "chat_requests",
                "message_data": {"message": "Hello"},
                "status": "pending",
            }
            
            with patch("app.main.republish_to_original_topic") as mock_republish:
                mock_republish.return_value = None
                
                with patch("app.main.mark_dlq_retried") as mock_mark:
                    mock_mark.return_value = None
                    
                    response = await async_client.post(f"/api/dlq/items/{dlq_id}/retry")
        
        assert response.status_code == 200
        mock_republish.assert_called_once()
        mock_mark.assert_called_once_with(dlq_id)
    
    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self, async_client):
        """Should return 404 when item not found."""
        with patch("app.main.get_dlq_item_detail") as mock_detail:
            mock_detail.return_value = None
            
            response = await async_client.post(f"/api/dlq/items/{ObjectId()}/retry")
        
        assert response.status_code == 404


class TestDLQResolveEndpoint:
    """Tests for POST /api/dlq/items/{id}/resolve endpoint."""
    
    @pytest.mark.asyncio
    async def test_resolves_item(self, async_client):
        """Should mark item as resolved."""
        dlq_id = str(ObjectId())
        
        with patch("app.main.get_dlq_item_detail") as mock_detail:
            mock_detail.return_value = {
                "id": dlq_id,
                "request_id": "req_123",
                "status": "pending",
            }
            
            with patch("app.main.mark_dlq_resolved") as mock_resolve:
                mock_resolve.return_value = None
                
                response = await async_client.post(f"/api/dlq/items/{dlq_id}/resolve")
        
        assert response.status_code == 200
        mock_resolve.assert_called_once_with(dlq_id)


class TestDLQDeleteEndpoint:
    """Tests for DELETE /api/dlq/items/{id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_deletes_item(self, async_client):
        """Should delete DLQ item."""
        dlq_id = str(ObjectId())
        
        with patch("app.main.delete_dlq_item") as mock_delete:
            mock_delete.return_value = True
            
            response = await async_client.delete(f"/api/dlq/items/{dlq_id}")
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self, async_client):
        """Should return 404 when item not found."""
        with patch("app.main.delete_dlq_item") as mock_delete:
            mock_delete.return_value = False
            
            response = await async_client.delete(f"/api/dlq/items/{ObjectId()}")
        
        assert response.status_code == 404


class TestDLQRetryAllEndpoint:
    """Tests for POST /api/dlq/retry-all endpoint."""
    
    @pytest.mark.asyncio
    async def test_retries_all_pending(self, async_client):
        """Should retry all pending items."""
        with patch("app.main.get_dlq_items") as mock_items:
            mock_items.return_value = [
                {"id": "1", "request_id": "req_1"},
                {"id": "2", "request_id": "req_2"},
            ]
            
            with patch("app.main.get_dlq_item_detail") as mock_detail:
                mock_detail.side_effect = [
                    {
                        "id": "1",
                        "request_id": "req_1",
                        "original_topic": "chat_requests",
                        "message_data": {"message": "Hello 1"},
                    },
                    {
                        "id": "2",
                        "request_id": "req_2",
                        "original_topic": "chat_requests",
                        "message_data": {"message": "Hello 2"},
                    },
                ]
                
                with patch("app.main.republish_to_original_topic") as mock_republish:
                    mock_republish.return_value = None
                    
                    with patch("app.main.mark_dlq_retried") as mock_mark:
                        mock_mark.return_value = None
                        
                        response = await async_client.post("/api/dlq/retry-all")
        
        assert response.status_code == 200
        data = response.json()
        assert data["retried"] == 2
        assert mock_republish.call_count == 2
