from motor.motor_asyncio import AsyncIOMotorClient
from app.config import get_settings

settings = get_settings()

client: AsyncIOMotorClient = None
db = None


async def connect_db():
    global client, db
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB_NAME]

    # Create indexes for analytics collections
    await _ensure_indexes()
    print("[Dataflow] Connected to MongoDB")


async def close_db():
    global client
    if client:
        client.close()
        print("[Dataflow] Disconnected from MongoDB")


def get_db():
    return db


async def _ensure_indexes():
    """Create indexes for analytics collections for efficient querying."""
    # analytics_events — high granularity event log
    await db.analytics_events.create_index([("timestamp", -1)])
    await db.analytics_events.create_index([("event_type", 1), ("timestamp", -1)])
    await db.analytics_events.create_index([("user_id", 1), ("timestamp", -1)])
    await db.analytics_events.create_index([("conversation_id", 1)])

    # analytics_metrics — aggregated metrics
    await db.analytics_metrics.create_index([("time_bucket", -1)])
    await db.analytics_metrics.create_index([("metric", 1), ("time_bucket", -1)])
    await db.analytics_metrics.create_index([
        ("metric", 1), ("model", 1), ("time_bucket", -1)
    ])

    # time_series — time-series data
    await db.time_series.create_index([("timestamp", -1)])
    await db.time_series.create_index([("series", 1), ("timestamp", -1)])

    print("[Dataflow] MongoDB indexes ensured")
