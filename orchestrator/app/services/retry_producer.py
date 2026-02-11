"""
Kafka producer for retry queue.

Used by orchestrator to:
- Send failed messages to retry queue
- Re-publish DLQ items for retry
"""
import json
from aiokafka import AIOKafkaProducer
from app.config import get_settings

settings = get_settings()

_retry_producer: AIOKafkaProducer = None


async def init_retry_producer():
    """Initialize Kafka producer for retry queue."""
    global _retry_producer
    
    _retry_producer = AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    
    await _retry_producer.start()
    print("[Orchestrator] Retry producer initialized")


async def stop_retry_producer():
    """Stop retry producer."""
    global _retry_producer
    if _retry_producer:
        await _retry_producer.stop()
        print("[Orchestrator] Retry producer stopped")


async def publish_to_retry_queue(data: dict):
    """
    Publish message to retry queue.
    
    Message will be picked up by consumer after backoff delay.
    """
    global _retry_producer
    
    if not _retry_producer:
        await init_retry_producer()
    
    await _retry_producer.send_and_wait(
        settings.KAFKA_RETRY_TOPIC,
        value=data,
    )
    
    retry_count = data.get("_retry", {}).get("retry_count", 0)
    request_id = data.get("request_id", "unknown")
    print(f"[Retry] Published to retry queue: request_id={request_id}, retry_count={retry_count}")


async def republish_to_original_topic(topic: str, data: dict):
    """
    Re-publish message to original topic (for DLQ retry).
    
    This bypasses the retry queue and sends directly to original topic.
    """
    global _retry_producer
    
    if not _retry_producer:
        await init_retry_producer()
    
    await _retry_producer.send_and_wait(topic, value=data)
    
    request_id = data.get("request_id", "unknown")
    print(f"[DLQ] Re-published to {topic}: request_id={request_id}")
