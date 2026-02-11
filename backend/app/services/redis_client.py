import json
import redis.asyncio as redis
from app.config import get_settings

settings = get_settings()

redis_client: redis.Redis = None


async def connect_redis():
    global redis_client
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    await redis_client.ping()
    print("[Backend] Connected to Redis")


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
        print("[Backend] Disconnected from Redis")


async def get_result(request_id: str) -> dict | None:
    """Get processing result from Redis. Returns None if not ready."""
    raw = await redis_client.get(f"result:{request_id}")
    if raw:
        return json.loads(raw)
    return None


async def delete_result(request_id: str):
    """Delete result from Redis (cleanup after finished)."""
    await redis_client.delete(f"result:{request_id}")
