"""
Dead Letter Queue (DLQ) handler.

Stores failed messages that exceeded retry limit in MongoDB.
Provides methods to:
- Save to DLQ
- List DLQ items
- Retry from DLQ
- Delete from DLQ
"""
from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from pydantic import BaseModel

from app.database import get_db
from app.config import get_settings

settings = get_settings()


class DLQItem(BaseModel):
    """Dead Letter Queue item schema."""
    id: str
    request_id: str
    original_topic: str
    message_data: dict
    error: str
    retry_count: int
    first_failed_at: datetime
    last_failed_at: datetime
    status: str  # "pending" | "retried" | "resolved"


async def save_to_dlq(
    request_id: str,
    original_topic: str,
    message_data: dict,
    error: str,
    retry_count: int,
) -> str:
    """
    Save failed message to Dead Letter Queue.
    
    Returns: DLQ item ID
    """
    db = get_db()
    
    # Check if already exists (idempotency)
    existing = await db.dead_letter_queue.find_one({"request_id": request_id})
    if existing:
        # Update existing entry
        await db.dead_letter_queue.update_one(
            {"request_id": request_id},
            {
                "$set": {
                    "last_error": error,
                    "retry_count": retry_count,
                    "last_failed_at": datetime.utcnow(),
                },
                "$push": {
                    "error_history": {
                        "error": error,
                        "timestamp": datetime.utcnow(),
                    }
                }
            }
        )
        print(f"[DLQ] Updated existing entry for request_id={request_id}")
        return str(existing["_id"])
    
    # Create new entry
    dlq_item = {
        "request_id": request_id,
        "original_topic": original_topic,
        "message_data": message_data,
        "last_error": error,
        "retry_count": retry_count,
        "error_history": [
            {"error": error, "timestamp": datetime.utcnow()}
        ],
        "first_failed_at": datetime.utcnow(),
        "last_failed_at": datetime.utcnow(),
        "status": "pending",  # pending | retried | resolved
        "created_at": datetime.utcnow(),
    }
    
    result = await db.dead_letter_queue.insert_one(dlq_item)
    print(f"[DLQ] Saved to DLQ: request_id={request_id}, error={error[:100]}")
    
    return str(result.inserted_id)


async def get_dlq_items(
    status: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
) -> List[dict]:
    """
    Get DLQ items with optional filtering.
    """
    db = get_db()
    
    query = {}
    if status:
        query["status"] = status
    
    cursor = db.dead_letter_queue.find(query).sort("last_failed_at", -1).skip(skip).limit(limit)
    
    items = []
    async for item in cursor:
        items.append({
            "id": str(item["_id"]),
            "request_id": item["request_id"],
            "original_topic": item["original_topic"],
            "last_error": item["last_error"],
            "retry_count": item["retry_count"],
            "first_failed_at": item["first_failed_at"].isoformat(),
            "last_failed_at": item["last_failed_at"].isoformat(),
            "status": item["status"],
            "error_count": len(item.get("error_history", [])),
        })
    
    return items


async def get_dlq_item_detail(dlq_id: str) -> Optional[dict]:
    """Get full DLQ item detail including message data."""
    db = get_db()
    
    try:
        item = await db.dead_letter_queue.find_one({"_id": ObjectId(dlq_id)})
    except:
        return None
    
    if not item:
        return None
    
    return {
        "id": str(item["_id"]),
        "request_id": item["request_id"],
        "original_topic": item["original_topic"],
        "message_data": item["message_data"],
        "last_error": item["last_error"],
        "retry_count": item["retry_count"],
        "error_history": item.get("error_history", []),
        "first_failed_at": item["first_failed_at"].isoformat(),
        "last_failed_at": item["last_failed_at"].isoformat(),
        "status": item["status"],
    }


async def mark_dlq_retried(dlq_id: str):
    """Mark DLQ item as retried."""
    db = get_db()
    await db.dead_letter_queue.update_one(
        {"_id": ObjectId(dlq_id)},
        {
            "$set": {
                "status": "retried",
                "retried_at": datetime.utcnow(),
            }
        }
    )


async def mark_dlq_resolved(dlq_id: str):
    """Mark DLQ item as resolved (manually handled)."""
    db = get_db()
    await db.dead_letter_queue.update_one(
        {"_id": ObjectId(dlq_id)},
        {
            "$set": {
                "status": "resolved",
                "resolved_at": datetime.utcnow(),
            }
        }
    )


async def delete_dlq_item(dlq_id: str) -> bool:
    """Delete DLQ item."""
    db = get_db()
    result = await db.dead_letter_queue.delete_one({"_id": ObjectId(dlq_id)})
    return result.deleted_count > 0


async def get_dlq_stats() -> dict:
    """Get DLQ statistics."""
    db = get_db()
    
    pipeline = [
        {
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }
        }
    ]
    
    stats = {"pending": 0, "retried": 0, "resolved": 0, "total": 0}
    
    async for doc in db.dead_letter_queue.aggregate(pipeline):
        status = doc["_id"]
        count = doc["count"]
        stats[status] = count
        stats["total"] += count
    
    # Get topic breakdown
    topic_pipeline = [
        {"$match": {"status": "pending"}},
        {"$group": {"_id": "$original_topic", "count": {"$sum": 1}}}
    ]
    
    stats["by_topic"] = {}
    async for doc in db.dead_letter_queue.aggregate(topic_pipeline):
        stats["by_topic"][doc["_id"]] = doc["count"]
    
    return stats
