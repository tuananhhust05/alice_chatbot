"""
Tests for kafka_producer service.
"""
import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock


class TestPublishChatRequest:
    """Tests for publish_chat_request function."""
    
    @pytest.mark.asyncio
    async def test_publishes_message_with_request_id(self):
        from app.services import kafka_producer
        
        mock_producer = AsyncMock()
        mock_producer.send_and_wait = AsyncMock()
        
        with patch.object(kafka_producer, "producer", mock_producer):
            with patch.object(kafka_producer, "settings") as mock_settings:
                mock_settings.KAFKA_CHAT_TOPIC = "chat_requests"
                
                await kafka_producer.publish_chat_request(
                    "req_123",
                    {"message": "Hello", "user_id": "user@test.com"}
                )
        
        mock_producer.send_and_wait.assert_called_once()
        call_args = mock_producer.send_and_wait.call_args
        
        assert call_args[0][0] == "chat_requests"
        assert call_args[0][1]["request_id"] == "req_123"
        assert call_args[0][1]["message"] == "Hello"
    
    @pytest.mark.asyncio
    async def test_includes_all_data_fields(self):
        from app.services import kafka_producer
        
        mock_producer = AsyncMock()
        mock_producer.send_and_wait = AsyncMock()
        
        data = {
            "message": "Test message",
            "user_id": "user@example.com",
            "conversation_id": "conv_456",
            "generate_title": True,
        }
        
        with patch.object(kafka_producer, "producer", mock_producer):
            with patch.object(kafka_producer, "settings") as mock_settings:
                mock_settings.KAFKA_CHAT_TOPIC = "chat_requests"
                
                await kafka_producer.publish_chat_request("req_789", data)
        
        sent_message = mock_producer.send_and_wait.call_args[0][1]
        
        assert sent_message["message"] == "Test message"
        assert sent_message["user_id"] == "user@example.com"
        assert sent_message["conversation_id"] == "conv_456"
        assert sent_message["generate_title"] == True


class TestPublishFileRequest:
    """Tests for publish_file_request function."""
    
    @pytest.mark.asyncio
    async def test_publishes_to_file_topic(self):
        from app.services import kafka_producer
        
        mock_producer = AsyncMock()
        mock_producer.send_and_wait = AsyncMock()
        
        with patch.object(kafka_producer, "producer", mock_producer):
            with patch.object(kafka_producer, "settings") as mock_settings:
                mock_settings.KAFKA_FILE_TOPIC = "file_requests"
                
                await kafka_producer.publish_file_request(
                    "file_req_123",
                    {"file_id": "file_456", "action": "process"}
                )
        
        call_args = mock_producer.send_and_wait.call_args
        assert call_args[0][0] == "file_requests"
        assert call_args[0][1]["request_id"] == "file_req_123"


class TestPublishRagdataRequest:
    """Tests for publish_ragdata_request function."""
    
    @pytest.mark.asyncio
    async def test_publishes_to_ragdata_topic(self):
        from app.services import kafka_producer
        
        mock_producer = AsyncMock()
        mock_producer.send_and_wait = AsyncMock()
        
        with patch.object(kafka_producer, "producer", mock_producer):
            await kafka_producer.publish_ragdata_request(
                "rag_req_123",
                {"file_id": "file_789", "content": "Document text"}
            )
        
        call_args = mock_producer.send_and_wait.call_args
        assert call_args[0][0] == "ragdata_requests"
        assert call_args[0][1]["request_id"] == "rag_req_123"


class TestPublishRagdataDelete:
    """Tests for publish_ragdata_delete function."""
    
    @pytest.mark.asyncio
    async def test_publishes_delete_action(self):
        from app.services import kafka_producer
        
        mock_producer = AsyncMock()
        mock_producer.send_and_wait = AsyncMock()
        
        with patch.object(kafka_producer, "producer", mock_producer):
            await kafka_producer.publish_ragdata_delete("file_to_delete")
        
        call_args = mock_producer.send_and_wait.call_args
        assert call_args[0][0] == "ragdata_requests"
        assert call_args[0][1]["action"] == "delete"
        assert call_args[0][1]["file_id"] == "file_to_delete"


class TestConnectKafka:
    """Tests for connect_kafka function."""
    
    @pytest.mark.asyncio
    async def test_retries_on_failure(self):
        from app.services import kafka_producer
        
        call_count = 0
        
        async def mock_start():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Connection failed")
        
        with patch("app.services.kafka_producer.AIOKafkaProducer") as MockProducer:
            mock_instance = AsyncMock()
            mock_instance.start = mock_start
            MockProducer.return_value = mock_instance
            
            with patch("asyncio.sleep", new_callable=AsyncMock):
                await kafka_producer.connect_kafka()
        
        assert call_count == 3  # Succeeded on 3rd attempt


class TestCloseKafka:
    """Tests for close_kafka function."""
    
    @pytest.mark.asyncio
    async def test_stops_producer(self):
        from app.services import kafka_producer
        
        mock_producer = AsyncMock()
        mock_producer.stop = AsyncMock()
        
        with patch.object(kafka_producer, "producer", mock_producer):
            await kafka_producer.close_kafka()
        
        mock_producer.stop.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handles_none_producer(self):
        from app.services import kafka_producer
        
        with patch.object(kafka_producer, "producer", None):
            # Should not raise error
            await kafka_producer.close_kafka()
