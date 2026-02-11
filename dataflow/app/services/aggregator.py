"""
Aggregate metrics from transformed events.
- Group by time windows
- Calculate statistics (avg, p50, p95, p99, count, sum)
- Write to analytics_metrics + time_series collections
"""
from datetime import datetime, timezone, timedelta
from app.database import get_db
from app.config import get_settings

settings = get_settings()


async def aggregate_llm_event(event: dict):
    """
    From a single LLM event, update:
    1. analytics_metrics — windowed aggregates
    2. time_series — per-minute data points
    """
    db = get_db()
    timestamp = event["timestamp"]
    model = event.get("model", "unknown")
    latency = event.get("latency_ms", 0)
    token_total = event.get("token_total", 0)
    token_prompt = event.get("token_prompt", 0)
    token_completion = event.get("token_completion", 0)
    success = event.get("success", True)

    # Time bucket (round down to METRIC_WINDOW_MINUTES)
    window = settings.METRIC_WINDOW_MINUTES
    bucket = _time_bucket(timestamp, window)
    minute_bucket = _time_bucket(timestamp, 1)

    # --- analytics_metrics: upsert aggregated metrics ---

    # 1. Request count
    await db.analytics_metrics.update_one(
        {"metric": "request_count", "model": model, "time_bucket": bucket},
        {
            "$inc": {"value": 1},
            "$set": {"updated_at": datetime.now(timezone.utc)},
            "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
        },
        upsert=True,
    )

    # 2. Success/error count
    status_metric = "success_count" if success else "error_count"
    await db.analytics_metrics.update_one(
        {"metric": status_metric, "model": model, "time_bucket": bucket},
        {
            "$inc": {"value": 1},
            "$set": {"updated_at": datetime.now(timezone.utc)},
            "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
        },
        upsert=True,
    )

    # 3. Latency — store in array for percentile calculation
    await db.analytics_metrics.update_one(
        {"metric": "latency_samples", "model": model, "time_bucket": bucket},
        {
            "$push": {"samples": latency},
            "$set": {"updated_at": datetime.now(timezone.utc)},
            "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
        },
        upsert=True,
    )

    # 4. Token usage
    await db.analytics_metrics.update_one(
        {"metric": "token_usage", "model": model, "time_bucket": bucket},
        {
            "$inc": {
                "total": token_total,
                "prompt": token_prompt,
                "completion": token_completion,
            },
            "$set": {"updated_at": datetime.now(timezone.utc)},
            "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
        },
        upsert=True,
    )

    # 5. Cost estimation (Groq pricing rough estimate: $0.59/$0.79 per 1M tokens)
    cost_prompt = token_prompt * 0.00000059
    cost_completion = token_completion * 0.00000079
    cost_total = cost_prompt + cost_completion

    await db.analytics_metrics.update_one(
        {"metric": "cost_estimate", "model": model, "time_bucket": bucket},
        {
            "$inc": {"value": cost_total},
            "$set": {"updated_at": datetime.now(timezone.utc)},
            "$setOnInsert": {"created_at": datetime.now(timezone.utc), "currency": "USD"},
        },
        upsert=True,
    )

    # --- time_series: per-minute data points ---

    await db.time_series.update_one(
        {"series": "requests_per_minute", "model": model, "timestamp": minute_bucket},
        {
            "$inc": {"count": 1},
            "$set": {"updated_at": datetime.now(timezone.utc)},
            "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
        },
        upsert=True,
    )

    await db.time_series.update_one(
        {"series": "latency_per_minute", "model": model, "timestamp": minute_bucket},
        {
            "$push": {"values": latency},
            "$inc": {"count": 1, "sum": latency},
            "$set": {"updated_at": datetime.now(timezone.utc)},
            "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
        },
        upsert=True,
    )

    await db.time_series.update_one(
        {"series": "tokens_per_minute", "model": model, "timestamp": minute_bucket},
        {
            "$inc": {"total": token_total, "prompt": token_prompt, "completion": token_completion},
            "$set": {"updated_at": datetime.now(timezone.utc)},
            "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
        },
        upsert=True,
    )

    if not success:
        await db.time_series.update_one(
            {"series": "errors_per_minute", "model": model, "timestamp": minute_bucket},
            {
                "$inc": {"count": 1},
                "$set": {"updated_at": datetime.now(timezone.utc)},
                "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
            },
            upsert=True,
        )


async def aggregate_file_event(event: dict):
    """Aggregate file processing metrics."""
    db = get_db()
    timestamp = event["timestamp"]
    file_type = event.get("file_type", "unknown")
    latency = event.get("latency_ms", 0)
    file_size = event.get("file_size", 0)
    chunk_count = event.get("chunk_count", 0)
    success = event.get("success", True)

    window = settings.METRIC_WINDOW_MINUTES
    bucket = _time_bucket(timestamp, window)
    minute_bucket = _time_bucket(timestamp, 1)

    # File processing count
    await db.analytics_metrics.update_one(
        {"metric": "file_processed_count", "file_type": file_type, "time_bucket": bucket},
        {
            "$inc": {"value": 1, "total_size": file_size, "total_chunks": chunk_count},
            "$set": {"updated_at": datetime.now(timezone.utc)},
            "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
        },
        upsert=True,
    )

    # File processing latency
    await db.analytics_metrics.update_one(
        {"metric": "file_latency_samples", "file_type": file_type, "time_bucket": bucket},
        {
            "$push": {"samples": latency},
            "$set": {"updated_at": datetime.now(timezone.utc)},
            "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
        },
        upsert=True,
    )

    # Time-series
    await db.time_series.update_one(
        {"series": "files_per_minute", "file_type": file_type, "timestamp": minute_bucket},
        {
            "$inc": {"count": 1, "total_size": file_size},
            "$set": {"updated_at": datetime.now(timezone.utc)},
            "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
        },
        upsert=True,
    )


async def calculate_statistics():
    """
    Periodic job: calculate P50/P95/P99 from latency samples.
    Called after each event for now; in production use scheduled tasks.
    """
    db = get_db()

    # Find latency_samples from last window
    window = settings.METRIC_WINDOW_MINUTES
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window * 2)

    cursor = db.analytics_metrics.find({
        "metric": "latency_samples",
        "time_bucket": {"$gte": cutoff},
    })

    async for doc in cursor:
        samples = sorted(doc.get("samples", []))
        if not samples:
            continue

        n = len(samples)
        stats = {
            "p50": samples[int(n * 0.50)] if n > 0 else 0,
            "p95": samples[int(n * 0.95)] if n > 1 else samples[-1],
            "p99": samples[int(n * 0.99)] if n > 2 else samples[-1],
            "avg": sum(samples) / n,
            "min": samples[0],
            "max": samples[-1],
            "count": n,
        }

        await db.analytics_metrics.update_one(
            {
                "metric": "latency_stats",
                "model": doc.get("model", "unknown"),
                "time_bucket": doc["time_bucket"],
            },
            {
                "$set": {**stats, "updated_at": datetime.now(timezone.utc)},
                "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
            },
            upsert=True,
        )


def _time_bucket(timestamp: datetime, window_minutes: int) -> datetime:
    """Round timestamp down to nearest window bucket."""
    if not isinstance(timestamp, datetime):
        timestamp = datetime.now(timezone.utc)
    # Ensure timezone-aware
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    minute = (timestamp.minute // window_minutes) * window_minutes
    return timestamp.replace(minute=minute, second=0, microsecond=0)
