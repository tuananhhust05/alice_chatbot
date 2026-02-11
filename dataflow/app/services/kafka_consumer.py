"""
Dataflow Kafka consumer — consumes events from kafkaflow,
transforms, aggregates, and writes to MongoDB analytics collections.
"""
import json
import asyncio
from aiokafka import AIOKafkaConsumer
from app.config import get_settings
from app.database import get_db
from app.services.transformer import (
    transform_llm_event,
    transform_file_event,
    transform_generic_event,
)
from app.services.aggregator import (
    aggregate_llm_event,
    aggregate_file_event,
    calculate_statistics,
)

settings = get_settings()

consumer: AIOKafkaConsumer = None
_consumer_task: asyncio.Task = None
_semaphore: asyncio.Semaphore = None

# Counters for logging
_processed_count = 0


async def start_consumer():
    """Start kafkaflow consumer."""
    global consumer, _consumer_task, _semaphore

    _semaphore = asyncio.Semaphore(settings.MAX_WORKERS)

    consumer = AIOKafkaConsumer(
        settings.KAFKAFLOW_EVENTS_TOPIC,
        settings.KAFKAFLOW_LLM_TOPIC,
        settings.KAFKAFLOW_FILE_TOPIC,
        bootstrap_servers=settings.KAFKAFLOW_BOOTSTRAP_SERVERS,
        group_id=settings.KAFKAFLOW_CONSUMER_GROUP,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",
        enable_auto_commit=True,
    )

    for attempt in range(30):
        try:
            await consumer.start()
            print(f"[Dataflow] Kafka consumer started (topics: {settings.KAFKAFLOW_LLM_TOPIC}, {settings.KAFKAFLOW_FILE_TOPIC}, {settings.KAFKAFLOW_EVENTS_TOPIC})")
            break
        except Exception as e:
            print(f"[Dataflow] Kafkaflow not ready (attempt {attempt+1}/30): {e}")
            await asyncio.sleep(2)
    else:
        print("[Dataflow] ERROR: Could not connect to kafkaflow after 30 attempts")
        return

    _consumer_task = asyncio.create_task(_consume_loop())


async def _consume_loop():
    """Main consume loop."""
    try:
        async for msg in consumer:
            asyncio.create_task(_process_with_semaphore(msg))
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"[Dataflow] Consumer loop error: {e}")


async def _process_with_semaphore(msg):
    async with _semaphore:
        await _process_message(msg)


async def _process_message(msg):
    """Full pipeline: Transform → Store Event → Aggregate → Statistics."""
    global _processed_count
    topic = msg.topic
    raw_data = msg.value

    try:
        db = get_db()

        # 1. Transform
        if topic == settings.KAFKAFLOW_LLM_TOPIC:
            event = transform_llm_event(raw_data)
        elif topic == settings.KAFKAFLOW_FILE_TOPIC:
            event = transform_file_event(raw_data)
        else:
            event = transform_generic_event(raw_data)

        # 2. Store transformed event (analytics_events)
        await db.analytics_events.insert_one(event)

        # 3. Aggregate metrics
        if topic == settings.KAFKAFLOW_LLM_TOPIC:
            await aggregate_llm_event(event)
            # 4. Calculate statistics (percentiles)
            await calculate_statistics()

        elif topic == settings.KAFKAFLOW_FILE_TOPIC:
            await aggregate_file_event(event)

        _processed_count += 1
        if _processed_count % 10 == 0:
            print(f"[Dataflow] Processed {_processed_count} events")

    except Exception as e:
        print(f"[Dataflow] Error processing event: {e}")
        # Store failed event for retry/debug
        try:
            await db.analytics_events.insert_one({
                "event_type": "PROCESSING_ERROR",
                "raw_data": raw_data,
                "error": str(e),
                "topic": topic,
            })
        except Exception:
            pass


async def stop_consumer():
    global consumer, _consumer_task
    if _consumer_task:
        _consumer_task.cancel()
        try:
            await _consumer_task
        except asyncio.CancelledError:
            pass
    if consumer:
        await consumer.stop()
        print(f"[Dataflow] Consumer stopped (total processed: {_processed_count})")
