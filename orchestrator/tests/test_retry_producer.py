"""
Tests for retry_producer service.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestPublishToRetryQueue:
    """Tests for publish_to_retry_queue function."""
    
    @pytest.mark.asyncio
    async def test_publishes_to_retry_topic(self):
        """Should publish message to retry topic."""
        from app.services import retry_producer
        
        mock_producer = AsyncMock()
        mock_producer.send_and_wait = AsyncMock()
        
        with patch.object(retry_producer, "_retry_producer", mock_producer):
            with patch.object(retry_producer, "settings") as mock_settings:
                mock_settings.KAFKA_RETRY_TOPIC = "retry_requests"
                
                await retry_producer.publish_to_retry_queue({
                    "request_id": "req_123",
                    "message": "Hello",
                    "_retry": {"retry_count": 1},
                })
        
        mock_producer.send_and_wait.assert_called_once()
        call_args = mock_producer.send_and_wait.call_args
        
        # Implementation uses positional args: send_and_wait(topic, value=data)
        assert call_args[0][0] == "retry_requests"
    
    @pytest.mark.asyncio
    async def test_initializes_producer_if_needed(self):
        """Should initialize producer if not already done."""
        from app.services import retry_producer
        
        with patch.object(retry_producer, "_retry_producer", None):
            with patch.object(retry_producer, "init_retry_producer") as mock_init:
                mock_init.return_value = None
                
                # Create a new mock producer after init
                async def set_producer():
                    retry_producer._retry_producer = AsyncMock()
                    retry_producer._retry_producer.send_and_wait = AsyncMock()
                
                mock_init.side_effect = set_producer
                
                with patch.object(retry_producer, "settings") as mock_settings:
                    mock_settings.KAFKA_RETRY_TOPIC = "retry_requests"
                    
                    await retry_producer.publish_to_retry_queue({"request_id": "req_123"})
                
                mock_init.assert_called_once()


class TestRepublishToOriginalTopic:
    """Tests for republish_to_original_topic function."""
    
    @pytest.mark.asyncio
    async def test_publishes_to_specified_topic(self):
        """Should publish to the specified original topic."""
        from app.services import retry_producer
        
        mock_producer = AsyncMock()
        mock_producer.send_and_wait = AsyncMock()
        
        with patch.object(retry_producer, "_retry_producer", mock_producer):
            await retry_producer.republish_to_original_topic(
                topic="chat_requests",
                data={"request_id": "req_123", "message": "Hello"},
            )
        
        mock_producer.send_and_wait.assert_called_once()
        call_args = mock_producer.send_and_wait.call_args
        
        # Implementation uses: send_and_wait(topic, value=data)
        assert call_args[0][0] == "chat_requests"
        assert call_args[1]["value"]["request_id"] == "req_123"


class TestInitRetryProducer:
    """Tests for init_retry_producer function."""
    
    @pytest.mark.asyncio
    async def test_creates_kafka_producer(self):
        """Should create and start Kafka producer."""
        from app.services import retry_producer
        
        mock_producer = AsyncMock()
        mock_producer.start = AsyncMock()
        
        with patch("app.services.retry_producer.AIOKafkaProducer") as MockProducer:
            MockProducer.return_value = mock_producer
            
            await retry_producer.init_retry_producer()
        
        mock_producer.start.assert_called_once()


class TestStopRetryProducer:
    """Tests for stop_retry_producer function."""
    
    @pytest.mark.asyncio
    async def test_stops_producer(self):
        """Should stop the producer."""
        from app.services import retry_producer
        
        mock_producer = AsyncMock()
        mock_producer.stop = AsyncMock()
        
        with patch.object(retry_producer, "_retry_producer", mock_producer):
            await retry_producer.stop_retry_producer()
        
        mock_producer.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handles_none_producer(self):
        """Should handle None producer gracefully."""
        from app.services import retry_producer
        
        with patch.object(retry_producer, "_retry_producer", None):
            # Should not raise
            await retry_producer.stop_retry_producer()
