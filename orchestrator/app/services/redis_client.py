import json
import redis.asyncio as redis
from app.config import get_settings

settings = get_settings()

redis_client: redis.Redis = None


async def connect_redis():
    global redis_client
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    await redis_client.ping()
    print("[Orchestrator] Connected to Redis")


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()
        print("[Orchestrator] Disconnected from Redis")


async def stream_update(request_id: str, reply: str, finished: int, extra: dict | None = None):
    """
    Update streaming result in Redis.
    - reply: accumulated full text so far
    - finished: 0 = still streaming, 1 = done
    - extra: optional fields (title, type, etc.) merged at finish
    """
    data = {
        "status": "completed" if finished else "streaming",
        "type": "chat",
        "reply": reply,
        "finished": finished,
    }
    if extra:
        data.update(extra)

    await redis_client.setex(
        f"result:{request_id}",
        settings.REDIS_RESULT_TTL,
        json.dumps(data),
    )


async def set_result(request_id: str, result: dict):
    """Store final processing result in Redis with TTL."""
    result["finished"] = 1
    await redis_client.setex(
        f"result:{request_id}",
        settings.REDIS_RESULT_TTL,
        json.dumps(result),
    )


async def set_error(request_id: str, error: str):
    """Store error in Redis."""
    await redis_client.setex(
        f"result:{request_id}",
        settings.REDIS_RESULT_TTL,
        json.dumps({"status": "error", "error": error, "finished": 1}),
    )


async def get_result(request_id: str) -> dict | None:
    """Get result from Redis."""
    result = await redis_client.get(f"result:{request_id}")
    if result:
        return json.loads(result)
    return None
