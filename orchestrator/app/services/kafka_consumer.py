"""
Kafka consumer with retry and DLQ support.

Flow:
1. Consume message from topic
2. Process message
3. If error:
   a. Check if retryable
   b. If yes and retry_count < max: send to retry queue
   c. If no or max reached: send to DLQ
"""
import json
import asyncio
from aiokafka import AIOKafkaConsumer
from app.config import get_settings, is_retryable_error
from app.services.redis_client import set_result, set_error
from app.services.chat_handler import handle_chat_request
from app.services.file_handler import handle_file_request
from app.services.ragdata_handler import handle_ragdata_request
from app.services.vectorstore import delete_ragdata_by_file
from app.services.retry_handler import (
    should_retry, create_retry_payload, extract_retry_info, wait_for_backoff
)
from app.services.retry_producer import publish_to_retry_queue, init_retry_producer, stop_retry_producer
from app.services.dlq_handler import save_to_dlq

settings = get_settings()

RAGDATA_TOPIC = "ragdata_requests"

consumer: AIOKafkaConsumer = None
_consumer_task: asyncio.Task = None
_semaphore: asyncio.Semaphore = None


async def start_consumer():
    """Start Kafka consumer with retry support."""
    global consumer, _consumer_task, _semaphore

    _semaphore = asyncio.Semaphore(settings.MAX_WORKERS)
    
    # Initialize retry producer
    await init_retry_producer()

    consumer = AIOKafkaConsumer(
        settings.KAFKA_CHAT_TOPIC,
        settings.KAFKA_FILE_TOPIC,
        settings.KAFKA_RETRY_TOPIC,  # Also consume from retry queue
        RAGDATA_TOPIC,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=settings.KAFKA_CONSUMER_GROUP,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",
        enable_auto_commit=True,
    )

    for attempt in range(30):
        try:
            await consumer.start()
            print(f"[Orchestrator] Kafka consumer started (max_workers={settings.MAX_WORKERS})")
            print(f"[Orchestrator] Retry config: max={settings.MAX_RETRY_COUNT}, backoff_base={settings.RETRY_BACKOFF_BASE}s")
            break
        except Exception as e:
            print(f"[Orchestrator] Kafka not ready (attempt {attempt+1}/30): {e}")
            await asyncio.sleep(2)
    else:
        print("[Orchestrator] ERROR: Could not connect to Kafka after 30 attempts")
        return

    _consumer_task = asyncio.create_task(_consume_loop())


async def _consume_loop():
    """Main consume loop — dispatches each message to a worker."""
    try:
        async for msg in consumer:
            asyncio.create_task(_process_with_semaphore(msg))
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"[Orchestrator] Consumer loop error: {e}")


async def _process_with_semaphore(msg):
    """Process a single Kafka message with concurrency limit."""
    async with _semaphore:
        await _process_message(msg)


async def _process_message(msg):
    """
    Route message to appropriate handler with retry support.
    
    If message is from retry queue, wait for backoff first.
    """
    topic = msg.topic
    data = msg.value
    request_id = data.get("request_id", "unknown")

    # Extract retry info if present
    original_data, retry_info = extract_retry_info(data.copy())
    
    # Determine original topic and retry count
    if topic == settings.KAFKA_RETRY_TOPIC:
        # This is a retry message
        if retry_info:
            original_topic = retry_info.get("original_topic", "unknown")
            retry_count = retry_info.get("retry_count", 1)
            
            # Wait for backoff delay
            await wait_for_backoff(retry_count)
        else:
            # Malformed retry message
            print(f"[Orchestrator] Malformed retry message: {request_id}")
            return
    else:
        # Normal message
        original_topic = topic
        retry_count = 0

    try:
        # Route to handler based on original topic
        if original_topic == settings.KAFKA_CHAT_TOPIC:
            result = await handle_chat_request({**original_data, "request_id": request_id})
            await set_result(request_id, {
                "status": "completed",
                "type": "chat",
                **result,
            })

        elif original_topic == settings.KAFKA_FILE_TOPIC:
            result = await handle_file_request({**original_data, "request_id": request_id})
            await set_result(request_id, {
                "status": "completed",
                "type": "file",
                **result,
            })

        elif original_topic == RAGDATA_TOPIC:
            # Check if it's a delete action
            if original_data.get("action") == "delete":
                file_id = original_data.get("file_id", "")
                if file_id:
                    await delete_ragdata_by_file(file_id)
                    print(f"[Orchestrator] Deleted RagData chunks for file_id={file_id}")
                return

            result = await handle_ragdata_request({**original_data, "request_id": request_id})
            await set_result(request_id, {
                "status": "completed",
                "type": "ragdata",
                **result,
            })

        else:
            print(f"[Orchestrator] Unknown topic: {original_topic}")

    except Exception as e:
        error_str = str(e)
        print(f"[Orchestrator] Error processing {request_id} (retry={retry_count}): {error_str[:200]}")
        
        # Determine if we should retry
        if should_retry(e, retry_count):
            # Send to retry queue
            retry_payload = create_retry_payload(
                original_data=original_data,
                original_topic=original_topic,
                error=error_str,
                retry_count=retry_count,
            )
            retry_payload["request_id"] = request_id
            
            await publish_to_retry_queue(retry_payload)
            
            # Update Redis with retry status
            await set_result(request_id, {
                "status": "retrying",
                "retry_count": retry_count + 1,
                "max_retry": settings.MAX_RETRY_COUNT,
                "error": error_str[:500],
            })
        else:
            # Send to DLQ
            await save_to_dlq(
                request_id=request_id,
                original_topic=original_topic,
                message_data=original_data,
                error=error_str,
                retry_count=retry_count,
            )
            
            # Set final error in Redis
            error_msg = error_str
            if retry_count >= settings.MAX_RETRY_COUNT:
                error_msg = f"Max retries ({settings.MAX_RETRY_COUNT}) exceeded. {error_str}"
            
            await set_error(request_id, error_msg)


async def stop_consumer():
    """Stop Kafka consumer and retry producer."""
    global consumer, _consumer_task
    
    if _consumer_task:
        _consumer_task.cancel()
        try:
            await _consumer_task
        except asyncio.CancelledError:
            pass
    
    if consumer:
        await consumer.stop()
        print("[Orchestrator] Kafka consumer stopped")
    
    await stop_retry_producer()