import os
import uuid
from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from contextlib import asynccontextmanager
from typing import Optional
from datetime import datetime

from app.database import connect_db, close_db, get_db
from app.services.vectorstore import connect_weaviate, close_weaviate
from app.services.llm import init_groq, init_embeddings
from app.services.redis_client import connect_redis, close_redis
from app.services.kafka_consumer import start_consumer, stop_consumer
from app.services.event_emitter import start_event_emitter, stop_event_emitter
from app.services.dlq_handler import (
    get_dlq_items, get_dlq_item_detail, get_dlq_stats,
    mark_dlq_resolved, delete_dlq_item, mark_dlq_retried
)
from app.services.retry_producer import republish_to_original_topic
from app.services.ragdata_handler import handle_ragdata_request
from app.services.vectorstore import delete_ragdata_by_file
from app.migrations import run_migrations
from app.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_db()
    await connect_weaviate()
    init_groq()
    init_embeddings()
    await run_migrations()
    await connect_redis()
    await start_event_emitter()
    await start_consumer()
    print("[Orchestrator] Service started — all-MiniLM-L6-v2 + Kafka + Redis + kafkaflow + Retry/DLQ")
    yield
    # Shutdown
    await stop_consumer()
    await stop_event_emitter()
    await close_redis()
    await close_weaviate()
    await close_db()
    print("[Orchestrator] Service stopped")


app = FastAPI(
    title="Alice Orchestrator",
    description="Kafka consumer — LLM/RAG with retry queue and DLQ support",
    version="5.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {
        "service": "orchestrator",
        "version": "5.0.0",
        "mode": "kafka-consumer",
        "features": ["retry-queue", "dlq", "exponential-backoff", "jitter"],
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "orchestrator"}


# ==================== DLQ ENDPOINTS ====================

@app.get("/api/dlq/stats")
async def dlq_stats():
    """Get DLQ statistics."""
    stats = await get_dlq_stats()
    return {
        **stats,
        "retry_config": {
            "max_retry": settings.MAX_RETRY_COUNT,
            "backoff_base": settings.RETRY_BACKOFF_BASE,
            "backoff_multiplier": settings.RETRY_BACKOFF_MULTIPLIER,
            "backoff_max": settings.RETRY_BACKOFF_MAX,
            "jitter_max": settings.RETRY_JITTER_MAX,
        }
    }


@app.get("/api/dlq/items")
async def list_dlq_items(
    status: Optional[str] = Query(None, description="Filter by status: pending, retried, resolved"),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
):
    """List DLQ items with optional filtering."""
    items = await get_dlq_items(status=status, limit=limit, skip=skip)
    return {"items": items, "count": len(items)}


@app.get("/api/dlq/items/{dlq_id}")
async def get_dlq_item(dlq_id: str):
    """Get DLQ item detail including message data."""
    item = await get_dlq_item_detail(dlq_id)
    if not item:
        raise HTTPException(status_code=404, detail="DLQ item not found")
    return item


@app.post("/api/dlq/items/{dlq_id}/retry")
async def retry_dlq_item(dlq_id: str):
    """
    Retry a DLQ item.
    
    Re-publishes the message to original topic for reprocessing.
    The retry count is reset.
    """
    item = await get_dlq_item_detail(dlq_id)
    if not item:
        raise HTTPException(status_code=404, detail="DLQ item not found")
    
    # Re-publish to original topic
    message_data = item["message_data"]
    message_data["request_id"] = item["request_id"]
    
    await republish_to_original_topic(
        topic=item["original_topic"],
        data=message_data,
    )
    
    # Mark as retried
    await mark_dlq_retried(dlq_id)
    
    return {
        "message": "DLQ item queued for retry",
        "request_id": item["request_id"],
        "topic": item["original_topic"],
    }


@app.post("/api/dlq/items/{dlq_id}/resolve")
async def resolve_dlq_item(dlq_id: str):
    """Mark DLQ item as resolved (manually handled)."""
    item = await get_dlq_item_detail(dlq_id)
    if not item:
        raise HTTPException(status_code=404, detail="DLQ item not found")
    
    await mark_dlq_resolved(dlq_id)
    
    return {"message": "DLQ item marked as resolved", "request_id": item["request_id"]}


@app.delete("/api/dlq/items/{dlq_id}")
async def remove_dlq_item(dlq_id: str):
    """Delete DLQ item permanently."""
    deleted = await delete_dlq_item(dlq_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="DLQ item not found")
    
    return {"message": "DLQ item deleted"}


@app.post("/api/dlq/retry-all")
async def retry_all_pending():
    """Retry all pending DLQ items."""
    items = await get_dlq_items(status="pending", limit=100)
    
    retried = 0
    for item in items:
        try:
            # Get full detail
            detail = await get_dlq_item_detail(item["id"])
            if detail:
                message_data = detail["message_data"]
                message_data["request_id"] = detail["request_id"]
                
                await republish_to_original_topic(
                    topic=detail["original_topic"],
                    data=message_data,
                )
                await mark_dlq_retried(item["id"])
                retried += 1
        except Exception as e:
            print(f"[DLQ] Failed to retry {item['id']}: {e}")
    
    return {"message": f"Retried {retried} DLQ items", "total": len(items), "retried": retried}


# ==================== RAG DATA ENDPOINTS ====================

# Allowed file extensions for RAG data
ALLOWED_RAG_EXTENSIONS = {"pdf", "txt", "csv", "docx", "xlsx"}


@app.post("/api/ragdata/upload")
async def upload_ragdata(file: UploadFile = File(...)):
    """
    Upload and process RAG data file.
    
    1. Save file to disk
    2. Create MongoDB record
    3. Extract text, chunk, embed, store in Weaviate
    4. Update MongoDB record with status
    
    Called by backend admin API.
    """
    db = get_db()
    
    # Validate file extension
    file_ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if file_ext not in ALLOWED_RAG_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{file_ext}' not supported. Allowed: {', '.join(ALLOWED_RAG_EXTENSIONS)}",
        )
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Check file size (10MB max)
    max_size = 10 * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(status_code=400, detail="File too large. Max: 10MB")
    
    # Save file to disk
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_id = str(uuid.uuid4())
    file_path = os.path.join(settings.UPLOAD_DIR, f"rag_{file_id}.{file_ext}")
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Create ragdata record with "processing" status
    rag_record = {
        "file_id": file_id,
        "original_name": file.filename,
        "file_type": file_ext,
        "file_path": file_path,
        "file_size": file_size,
        "chunk_count": 0,
        "status": "processing",
        "created_at": datetime.utcnow(),
    }
    result = await db.ragdata.insert_one(rag_record)
    record_id = str(result.inserted_id)
    
    # Process: extract → chunk → embed → store in Weaviate
    try:
        process_result = await handle_ragdata_request({
            "file_id": file_id,
            "record_id": record_id,
            "file_path": file_path,
            "file_type": file_ext,
            "original_name": file.filename,
        })
        
        return {
            "id": record_id,
            "file_id": file_id,
            "original_name": file.filename,
            "chunk_count": process_result["chunk_count"],
            "status": "completed",
        }
        
    except Exception as e:
        # Update record with error
        from bson import ObjectId
        await db.ragdata.update_one(
            {"_id": ObjectId(record_id)},
            {"$set": {
                "status": "failed",
                "error": str(e),
            }}
        )
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.delete("/api/ragdata/{file_id}")
async def delete_ragdata(file_id: str):
    """
    Delete RAG data by file_id.
    
    Removes from Weaviate only. MongoDB cleanup is handled by backend.
    """
    try:
        await delete_ragdata_by_file(file_id)
        return {"message": f"RAG data deleted for file_id: {file_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")
