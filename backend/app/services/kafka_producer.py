import json
import asyncio
from aiokafka import AIOKafkaProducer
from app.config import get_settings

settings = get_settings()

producer: AIOKafkaProducer = None


async def connect_kafka():
    """Start Kafka producer with retry."""
    global producer
    for attempt in range(30):
        try:
            producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
            await producer.start()
            print("[Backend] Kafka producer started")
            return
        except Exception as e:
            print(f"[Backend] Kafka not ready (attempt {attempt+1}/30): {e}")
            await asyncio.sleep(2)
    print("[Backend] ERROR: Could not connect to Kafka")


async def close_kafka():
    global producer
    if producer:
        await producer.stop()
        print("[Backend] Kafka producer stopped")


async def publish_chat_request(request_id: str, data: dict):
    """Publish chat request to Kafka."""
    message = {"request_id": request_id, **data}
    await producer.send_and_wait(settings.KAFKA_CHAT_TOPIC, message)


async def publish_file_request(request_id: str, data: dict):
    """Publish file processing request to Kafka."""
    message = {"request_id": request_id, **data}
    await producer.send_and_wait(settings.KAFKA_FILE_TOPIC, message)


async def publish_ragdata_request(request_id: str, data: dict):
    """Publish RAG data processing request to Kafka."""
    message = {"request_id": request_id, **data}
    await producer.send_and_wait("ragdata_requests", message)


async def publish_ragdata_delete(file_id: str):
    """Publish RAG data delete request to Kafka — orchestrator will clean Weaviate."""
    message = {"action": "delete", "file_id": file_id}
    await producer.send_and_wait("ragdata_requests", message)
