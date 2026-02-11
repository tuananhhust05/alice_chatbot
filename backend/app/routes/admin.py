"""Admin API — completely separate auth from user endpoints."""
import os
import uuid
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

from app.database import get_db
from app.config import get_settings
from app.services.admin_auth import verify_admin_credentials, create_admin_token, verify_admin_token
from app.security import (
    get_client_ip, 
    check_login_attempts, 
    record_failed_login, 
    clear_login_attempts,
    blacklist_ip,
    unblacklist_ip,
    get_blacklisted_ips,
    get_ip_statistics,
    log_security_event,
)

settings = get_settings()
router = APIRouter(prefix="/api/admin", tags=["admin"])


# ===== Admin Auth Dependency =====

async def require_admin(request: Request):
    """Dependency to verify admin token from cookie."""
    token = request.cookies.get("admin_token")
    if not token:
        raise HTTPException(status_code=401, detail="Admin authentication required")
    
    if not verify_admin_token(token):
        raise HTTPException(status_code=401, detail="Invalid or expired admin token")
    
    return True


# ===== Auth =====

class AdminLoginRequest(BaseModel):
    username: str
    password: str


class PromptUpdateRequest(BaseModel):
    system_prompt: str
    rag_prompt_template: str


class IPBlacklistRequest(BaseModel):
    ip: str
    reason: Optional[str] = ""
    ttl_hours: Optional[int] = 24  # Default 24 hours


class IPStatsRequest(BaseModel):
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    ip_filter: Optional[str] = None
    limit: Optional[int] = 100


@router.post("/login")
async def admin_login(request: AdminLoginRequest, raw_request: Request):
    """Admin login — returns JWT in cookie with brute-force protection."""
    client_ip = get_client_ip(raw_request)
    
    # Check brute-force protection
    is_allowed, attempts_remaining = await check_login_attempts(client_ip, request.username)
    if not is_allowed:
        log_security_event(
            event_type="admin_login_blocked",
            client_ip=client_ip,
            user_id=request.username,
            details={"reason": "too_many_attempts"},
            severity="warning"
        )
        raise HTTPException(
            status_code=429, 
            detail=f"Too many login attempts. Please try again in {settings.ADMIN_LOGIN_LOCKOUT_MINUTES} minutes."
        )
    
    if not verify_admin_credentials(request.username, request.password):
        # Record failed attempt
        await record_failed_login(client_ip, request.username)
        log_security_event(
            event_type="admin_login_failed",
            client_ip=client_ip,
            user_id=request.username,
            details={"attempts_remaining": attempts_remaining - 1},
            severity="warning"
        )
        raise HTTPException(status_code=401, detail="Invalid admin credentials")

    # Clear failed attempts on successful login
    await clear_login_attempts(client_ip, request.username)
    
    log_security_event(
        event_type="admin_login_success",
        client_ip=client_ip,
        user_id=request.username,
        details={},
        severity="info"
    )

    token = create_admin_token()

    response = JSONResponse(content={
        "message": "Admin login successful",
        "role": "admin",
    })
    response.set_cookie(
        key="admin_token",
        value=token,
        httponly=True,
        secure=settings.SECURE_COOKIES,
        samesite="lax" if not settings.SECURE_COOKIES else "strict",
        max_age=43200,  # 12 hours
    )
    return response


@router.post("/logout", dependencies=[Depends(require_admin)])
async def admin_logout():
    response = JSONResponse(content={"message": "Admin logged out"})
    response.delete_cookie("admin_token")
    return response


@router.get("/me", dependencies=[Depends(require_admin)])
async def admin_me(request: Request):
    """Check admin session."""
    return {"role": "admin", "username": settings.ADMIN_USERNAME}


# ===== Users =====

@router.get("/users", dependencies=[Depends(require_admin)])
async def list_users(skip: int = 0, limit: int = 50):
    db = get_db()
    cursor = db.users.find().sort("created_at", -1).skip(skip).limit(limit)
    users = []
    async for u in cursor:
        users.append({
            "id": str(u["_id"]),
            "email": u.get("email", ""),
            "name": u.get("name", ""),
            "picture": u.get("picture", ""),
            "created_at": u.get("created_at", ""),
            "updated_at": u.get("updated_at", ""),
        })
    total = await db.users.count_documents({})
    return {"users": users, "total": total}


@router.delete("/users/{user_id}", dependencies=[Depends(require_admin)])
async def delete_user(user_id: str):
    db = get_db()
    result = await db.users.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted"}


# ===== Conversations =====

@router.get("/conversations", dependencies=[Depends(require_admin)])
async def list_conversations(skip: int = 0, limit: int = 50, user_email: Optional[str] = None):
    db = get_db()
    query = {}
    if user_email:
        query["user_id"] = user_email

    cursor = db.conversations.find(query).sort("updated_at", -1).skip(skip).limit(limit)
    conversations = []
    async for c in cursor:
        conversations.append({
            "id": str(c["_id"]),
            "user_id": c.get("user_id", ""),
            "title": c.get("title", ""),
            "message_count": len(c.get("messages", [])),
            "file_count": len(c.get("file_ids", [])),
            "created_at": c.get("created_at", ""),
            "updated_at": c.get("updated_at", ""),
        })
    total = await db.conversations.count_documents(query)
    return {"conversations": conversations, "total": total}


@router.get("/conversations/{conversation_id}", dependencies=[Depends(require_admin)])
async def get_conversation_detail(conversation_id: str):
    db = get_db()
    c = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
    if not c:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = []
    for msg in c.get("messages", []):
        messages.append({
            "role": msg.get("role", ""),
            "content": msg.get("content", ""),
            "timestamp": str(msg.get("timestamp", "")),
        })

    return {
        "id": str(c["_id"]),
        "user_id": c.get("user_id", ""),
        "title": c.get("title", ""),
        "messages": messages,
        "file_ids": [str(f) for f in c.get("file_ids", [])],
        "created_at": c.get("created_at", ""),
        "updated_at": c.get("updated_at", ""),
    }


@router.delete("/conversations/{conversation_id}", dependencies=[Depends(require_admin)])
async def delete_conversation(conversation_id: str):
    db = get_db()
    result = await db.conversations.delete_one({"_id": ObjectId(conversation_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"message": "Conversation deleted"}


# ===== Analytics =====

@router.get("/analytics/overview", dependencies=[Depends(require_admin)])
async def analytics_overview():
    db = get_db()
    return {
        "users_total": await db.users.count_documents({}),
        "conversations_total": await db.conversations.count_documents({}),
        "files_total": await db.files.count_documents({}),
        "events_total": await db.analytics_events.count_documents({}),
        "llm_events": await db.analytics_events.count_documents({"event_type": "LLM_RESPONSE"}),
        "file_events": await db.analytics_events.count_documents({"event_type": "FILE_PROCESSED"}),
    }


@router.get("/analytics/metrics", dependencies=[Depends(require_admin)])
async def analytics_metrics(metric: Optional[str] = None, limit: int = 50):
    db = get_db()
    query = {}
    if metric:
        query["metric"] = metric

    cursor = db.analytics_metrics.find(query).sort("time_bucket", -1).limit(limit)
    metrics = []
    async for m in cursor:
        m["_id"] = str(m["_id"])
        if "time_bucket" in m and isinstance(m["time_bucket"], datetime):
            m["time_bucket"] = m["time_bucket"].isoformat()
        if "created_at" in m and isinstance(m["created_at"], datetime):
            m["created_at"] = m["created_at"].isoformat()
        if "updated_at" in m and isinstance(m["updated_at"], datetime):
            m["updated_at"] = m["updated_at"].isoformat()
        metrics.append(m)
    return {"metrics": metrics}


@router.get("/analytics/events", dependencies=[Depends(require_admin)])
async def analytics_events(event_type: Optional[str] = None, skip: int = 0, limit: int = 50):
    db = get_db()
    query = {}
    if event_type:
        query["event_type"] = event_type

    cursor = db.analytics_events.find(query).sort("timestamp", -1).skip(skip).limit(limit)
    events = []
    async for e in cursor:
        e["_id"] = str(e["_id"])
        for k, v in e.items():
            if isinstance(v, datetime):
                e[k] = v.isoformat()
        events.append(e)
    total = await db.analytics_events.count_documents(query)
    return {"events": events, "total": total}


@router.get("/analytics/timeseries", dependencies=[Depends(require_admin)])
async def analytics_timeseries(series: Optional[str] = None, limit: int = 100):
    db = get_db()
    query = {}
    if series:
        query["series"] = series

    cursor = db.time_series.find(query).sort("timestamp", -1).limit(limit)
    data = []
    async for d in cursor:
        d["_id"] = str(d["_id"])
        for k, v in d.items():
            if isinstance(v, datetime):
                d[k] = v.isoformat()
        data.append(d)
    return {"data": data}


# ===== Prompts =====

@router.get("/prompts", dependencies=[Depends(require_admin)])
async def get_prompts():
    db = get_db()
    prompt = await db.prompts.find_one({"key": "system_prompts"})
    if not prompt:
        return {
            "system_prompt": "",
            "rag_prompt_template": "",
        }
    return {
        "system_prompt": prompt.get("system_prompt", ""),
        "rag_prompt_template": prompt.get("rag_prompt_template", ""),
        "updated_at": str(prompt.get("updated_at", "")),
    }


@router.put("/prompts", dependencies=[Depends(require_admin)])
async def update_prompts(request: PromptUpdateRequest):
    db = get_db()
    await db.prompts.update_one(
        {"key": "system_prompts"},
        {
            "$set": {
                "system_prompt": request.system_prompt,
                "rag_prompt_template": request.rag_prompt_template,
                "updated_at": datetime.utcnow(),
            },
            "$setOnInsert": {"key": "system_prompts", "created_at": datetime.utcnow()},
        },
        upsert=True,
    )
    return {"message": "Prompts updated"}


# ===== RAG Data =====

# Global RAG KB: allow PDF, TXT, CSV, Word (.docx), Excel (.xlsx)
ALLOWED_RAG_EXTENSIONS = {"pdf", "txt", "csv", "docx", "xlsx"}


@router.get("/ragdata", dependencies=[Depends(require_admin)])
async def list_ragdata(skip: int = 0, limit: int = 50):
    db = get_db()
    cursor = db.ragdata.find().sort("created_at", -1).skip(skip).limit(limit)
    files = []
    async for f in cursor:
        files.append({
            "id": str(f["_id"]),
            "original_name": f.get("original_name", ""),
            "file_type": f.get("file_type", ""),
            "file_size": f.get("file_size", 0),
            "chunk_count": f.get("chunk_count", 0),
            "status": f.get("status", "processing"),
            "error": f.get("error"),
            "created_at": str(f.get("created_at", "")),
        })
    total = await db.ragdata.count_documents({})
    return {"files": files, "total": total}


@router.post("/ragdata/upload", dependencies=[Depends(require_admin)])
async def upload_ragdata(file: UploadFile = File(...)):
    """Upload RAG data file — forwards to orchestrator for processing."""
    import httpx
    
    # Validate file extension first
    file_ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if file_ext not in ALLOWED_RAG_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{file_ext}' not supported. Allowed: {', '.join(ALLOWED_RAG_EXTENSIONS)}",
        )
    
    # Read file content for size check
    content = await file.read()
    file_size = len(content)
    
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(status_code=400, detail=f"File too large. Max: {settings.MAX_FILE_SIZE_MB}MB")
    
    # Reset file position for forwarding
    await file.seek(0)
    
    # Forward to orchestrator
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            files = {"file": (file.filename, content, file.content_type or "application/octet-stream")}
            response = await client.post(
                f"{settings.ORCHESTRATOR_URL}/api/ragdata/upload",
                files=files,
            )
            
            if response.status_code != 200:
                error_detail = response.json().get("detail", "Unknown error")
                raise HTTPException(status_code=response.status_code, detail=error_detail)
            
            return response.json()
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Orchestrator service unavailable: {str(e)}")


@router.delete("/ragdata/{record_id}", dependencies=[Depends(require_admin)])
async def delete_ragdata(record_id: str):
    """Delete RAG data — removes from MongoDB and calls orchestrator to delete from Weaviate."""
    import httpx
    
    db = get_db()
    record = await db.ragdata.find_one({"_id": ObjectId(record_id)})
    if not record:
        raise HTTPException(status_code=404, detail="RAG data not found")

    file_id = record.get("file_id", "")

    # Delete file from disk (orchestrator's upload dir)
    file_path = record.get("file_path", "")
    if file_path and os.path.exists(file_path):
        os.remove(file_path)

    # Delete chunks from Weaviate via orchestrator
    if file_id:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{settings.ORCHESTRATOR_URL}/api/ragdata/{file_id}"
                )
                if response.status_code not in (200, 404):
                    print(f"[Backend] Orchestrator delete warning: {response.text}")
        except Exception as e:
            print(f"[Backend] Orchestrator delete error: {e}")

    # Delete from MongoDB
    await db.ragdata.delete_one({"_id": ObjectId(record_id)})

    return {"message": "RAG data deleted"}


# ===== IP Management =====

@router.get("/ip/stats", dependencies=[Depends(require_admin)])
async def get_ip_stats(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    ip_filter: Optional[str] = None,
    limit: int = 100,
):
    """Get IP access statistics."""
    stats = await get_ip_statistics(
        date_from=date_from,
        date_to=date_to,
        ip_filter=ip_filter,
        limit=limit,
    )
    return stats


@router.get("/ip/blacklist", dependencies=[Depends(require_admin)])
async def get_ip_blacklist():
    """Get list of blacklisted IPs."""
    ips = await get_blacklisted_ips()
    return {"blacklisted_ips": ips, "total": len(ips)}


@router.post("/ip/blacklist", dependencies=[Depends(require_admin)])
async def add_ip_to_blacklist(request: IPBlacklistRequest, raw_request: Request):
    """Add an IP to the blacklist."""
    client_ip = get_client_ip(raw_request)
    
    await blacklist_ip(
        ip=request.ip,
        reason=request.reason,
        ttl_seconds=request.ttl_hours * 3600 if request.ttl_hours else 0
    )
    
    log_security_event(
        event_type="ip_blacklisted",
        client_ip=client_ip,
        user_id="admin",
        details={"blocked_ip": request.ip, "reason": request.reason, "ttl_hours": request.ttl_hours},
        severity="warning"
    )
    
    return {"message": f"IP {request.ip} has been blacklisted", "ip": request.ip}


@router.delete("/ip/blacklist/{ip}", dependencies=[Depends(require_admin)])
async def remove_ip_from_blacklist(ip: str, raw_request: Request):
    """Remove an IP from the blacklist."""
    client_ip = get_client_ip(raw_request)
    
    await unblacklist_ip(ip)
    
    log_security_event(
        event_type="ip_unblacklisted",
        client_ip=client_ip,
        user_id="admin",
        details={"unblocked_ip": ip},
        severity="info"
    )
    
    return {"message": f"IP {ip} has been removed from blacklist", "ip": ip}


@router.get("/ip/messages", dependencies=[Depends(require_admin)])
async def get_messages_by_ip(
    ip: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
):
    """Get messages filtered by IP address."""
    db = get_db()
    
    query = {}
    if ip:
        query["client_ip"] = ip
    
    if date_from or date_to:
        query["timestamp"] = {}
        if date_from:
            query["timestamp"]["$gte"] = datetime.fromisoformat(date_from)
        if date_to:
            query["timestamp"]["$lte"] = datetime.fromisoformat(date_to + "T23:59:59")
    
    cursor = db.ip_messages.find(query).sort("timestamp", -1).skip(skip).limit(limit)
    
    messages = []
    async for msg in cursor:
        messages.append({
            "id": str(msg["_id"]),
            "ip": msg.get("client_ip", ""),
            "user_id": msg.get("user_id", ""),
            "conversation_id": msg.get("conversation_id", ""),
            "message_preview": msg.get("message_preview", "")[:100],
            "timestamp": msg.get("timestamp", ""),
        })
    
    total = await db.ip_messages.count_documents(query)
    
    return {
        "messages": messages,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/ip/summary", dependencies=[Depends(require_admin)])
async def get_ip_summary():
    """Get summary of IP activity."""
    db = get_db()
    
    # Get unique IPs from today's messages
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    pipeline = [
        {"$match": {"timestamp": {"$gte": today}}},
        {"$group": {
            "_id": "$client_ip",
            "message_count": {"$sum": 1},
            "unique_users": {"$addToSet": "$user_id"},
            "last_activity": {"$max": "$timestamp"},
        }},
        {"$sort": {"message_count": -1}},
        {"$limit": 50},
    ]
    
    ip_summary = []
    async for doc in db.ip_messages.aggregate(pipeline):
        ip_summary.append({
            "ip": doc["_id"],
            "message_count": doc["message_count"],
            "unique_users_count": len(doc["unique_users"]),
            "last_activity": doc["last_activity"],
        })
    
    # Get blacklisted IPs
    blacklisted = await get_blacklisted_ips()
    
    # Get total messages today
    total_messages_today = await db.ip_messages.count_documents({"timestamp": {"$gte": today}})
    
    # Get unique IPs today
    unique_ips_today = len(await db.ip_messages.distinct("client_ip", {"timestamp": {"$gte": today}}))
    
    return {
        "ip_activity": ip_summary,
        "blacklisted_ips": blacklisted,
        "total_messages_today": total_messages_today,
        "unique_ips_today": unique_ips_today,
    }
