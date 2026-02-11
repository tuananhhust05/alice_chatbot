from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.database import connect_db, close_db, get_db
from app.services.kafka_consumer import start_consumer, stop_consumer


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_db()
    await start_consumer()
    print("[Dataflow] Service started — consuming from kafkaflow, writing analytics to MongoDB")
    yield
    # Shutdown
    await stop_consumer()
    await close_db()
    print("[Dataflow] Service stopped")


app = FastAPI(
    title="Alice Dataflow",
    description="Analytics pipeline — transform, aggregate, time-series from orchestrator events",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {"service": "dataflow", "version": "1.0.0", "mode": "kafka-consumer"}


@app.get("/health")
async def health():
    db = get_db()
    event_count = await db.analytics_events.count_documents({})
    metric_count = await db.analytics_metrics.count_documents({})
    ts_count = await db.time_series.count_documents({})

    return {
        "status": "healthy",
        "service": "dataflow",
        "collections": {
            "analytics_events": event_count,
            "analytics_metrics": metric_count,
            "time_series": ts_count,
        },
    }


@app.get("/stats")
async def get_stats():
    """Quick stats overview from analytics data."""
    db = get_db()

    # Total events
    total_events = await db.analytics_events.count_documents({})
    llm_events = await db.analytics_events.count_documents({"event_type": "LLM_RESPONSE"})
    file_events = await db.analytics_events.count_documents({"event_type": "FILE_PROCESSED"})

    # Latest latency stats
    latest_stats = await db.analytics_metrics.find_one(
        {"metric": "latency_stats"},
        sort=[("time_bucket", -1)],
    )

    # Latest cost
    latest_cost = await db.analytics_metrics.find_one(
        {"metric": "cost_estimate"},
        sort=[("time_bucket", -1)],
    )

    return {
        "total_events": total_events,
        "llm_events": llm_events,
        "file_events": file_events,
        "latest_latency": {
            "avg": latest_stats.get("avg", 0) if latest_stats else 0,
            "p50": latest_stats.get("p50", 0) if latest_stats else 0,
            "p95": latest_stats.get("p95", 0) if latest_stats else 0,
            "p99": latest_stats.get("p99", 0) if latest_stats else 0,
        },
        "latest_cost_usd": latest_cost.get("value", 0) if latest_cost else 0,
    }
