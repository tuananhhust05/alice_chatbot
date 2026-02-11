"""
Event emitter — publishes analytics events to kafkaflow.
Non-blocking, fire-and-forget: errors here never affect user response.
"""
import json
import asyncio
import time
from datetime import datetime, timezone
from aiokafka import AIOKafkaProducer
from app.config import get_settings

settings = get_settings()

producer: AIOKafkaProducer = None


async def start_event_emitter():
    """Start Kafka producer for kafkaflow."""
    global producer
    for attempt in range(30):
        try:
            producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKAFLOW_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            )
            await producer.start()
            print("[Orchestrator] Event emitter started (kafkaflow)")
            return
        except Exception as e:
            print(f"[Orchestrator] Kafkaflow not ready (attempt {attempt+1}/30): {e}")
            await asyncio.sleep(2)
    print("[Orchestrator] WARNING: Could not connect to kafkaflow — events will be dropped")


async def stop_event_emitter():
    global producer
    if producer:
        await producer.stop()
        print("[Orchestrator] Event emitter stopped")


async def emit_llm_event(
    conversation_id: str,
    user_id: str,
    message: str,
    reply: str,
    model: str,
    latency_ms: int,
    token_prompt: int,
    token_completion: int,
    success: bool,
    has_rag: bool = False,
    title: str | None = None,
    error: str | None = None,
):
    """Emit LLM call event to kafkaflow."""
    if not producer:
        return

    event = {
        "event_type": "LLM_RESPONSE",
        "conversation_id": conversation_id,
        "user_id": user_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "latency_ms": latency_ms,
        "token_prompt": token_prompt,
        "token_completion": token_completion,
        "success": success,
        "has_rag": has_rag,
        "message_length": len(message),
        "reply_length": len(reply),
        "title": title,
        "error": error,
    }

    try:
        await producer.send_and_wait(settings.KAFKAFLOW_LLM_TOPIC, event)
    except Exception as e:
        print(f"[Orchestrator] Failed to emit LLM event: {e}")


async def emit_file_event(
    conversation_id: str,
    user_id: str,
    file_id: str,
    file_type: str,
    original_name: str,
    file_size: int,
    chunk_count: int,
    latency_ms: int,
    success: bool,
    error: str | None = None,
):
    """Emit file processing event to kafkaflow."""
    if not producer:
        return

    event = {
        "event_type": "FILE_PROCESSED",
        "conversation_id": conversation_id,
        "user_id": user_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "file_id": file_id,
        "file_type": file_type,
        "original_name": original_name,
        "file_size": file_size,
        "chunk_count": chunk_count,
        "latency_ms": latency_ms,
        "success": success,
        "error": error,
    }

    try:
        await producer.send_and_wait(settings.KAFKAFLOW_FILE_TOPIC, event)
    except Exception as e:
        print(f"[Orchestrator] Failed to emit file event: {e}")


async def emit_conversation_event(
    event_type: str,
    conversation_id: str,
    user_id: str,
    metadata: dict | None = None,
):
    """Emit conversation lifecycle event (created, deleted, etc.)."""
    if not producer:
        return

    event = {
        "event_type": event_type,
        "conversation_id": conversation_id,
        "user_id": user_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **(metadata or {}),
    }

    try:
        await producer.send_and_wait(settings.KAFKAFLOW_EVENTS_TOPIC, event)
    except Exception as e:
        print(f"[Orchestrator] Failed to emit conversation event: {e}")
