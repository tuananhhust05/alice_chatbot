import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import List
from datetime import datetime
from bson import ObjectId

from app.dependencies import get_current_user_dep
from app.models.chat import (
    ChatRequest, ChatSendResponse, Message,
    ConversationListItem, ConversationDetail,
)
from app.database import get_db
from app.services.kafka_producer import publish_chat_request
from app.security import validate_input, log_security_event, get_client_ip, track_ip_access

router = APIRouter(prefix="/api/chat", tags=["chat"])


async def save_ip_message(
    client_ip: str,
    user_id: str,
    conversation_id: str,
    message: str,
    user_agent: str = None,
):
    """Save IP tracking information for a message."""
    db = get_db()
    ip_record = {
        "client_ip": client_ip,
        "user_id": user_id,
        "conversation_id": conversation_id,
        "message_preview": message[:200] if message else "",
        "user_agent": user_agent,
        "timestamp": datetime.utcnow(),
    }
    await db.ip_messages.insert_one(ip_record)
    
    # Also track in Redis for real-time stats
    await track_ip_access(client_ip, "/api/chat/send", user_id)


@router.post("/send", response_model=ChatSendResponse)
async def send_message(
    request: ChatRequest,
    raw_request: Request,
    user: dict = Depends(get_current_user_dep),
):
    """
    Send message: save user msg to DB, publish to Kafka, return request_id.
    
    - request.message: Full message with file content (sent to LLM)
    - request.display_content: Short version for UI display (saved to DB)
    """
    db = get_db()
    user_id = user["email"]
    client_ip = get_client_ip(raw_request)
    user_agent = raw_request.headers.get("User-Agent", "")

    # ===== SECURITY: Input Validation =====
    is_valid, error_msg = validate_input(request.message)
    if not is_valid:
        log_security_event(
            event_type="invalid_input_blocked",
            client_ip=client_ip,
            user_id=user_id,
            details={"error": error_msg, "message_preview": request.message[:100]},
            severity="warning"
        )
        raise HTTPException(status_code=400, detail=error_msg)

    # Get or create conversation
    if request.conversation_id:
        try:
            conversation = await db.conversations.find_one({
                "_id": ObjectId(request.conversation_id),
                "user_id": user_id,
            })
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
        except Exception:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        # For title, use display_content or short version of message
        title_source = request.display_content or request.message.split("\n\nFile content:")[0]
        title_text = title_source[:50]
        if len(title_source) > 50:
            title_text += "..."
            
        conversation = {
            "user_id": user_id,
            "title": title_text,
            "messages": [],
            "file_ids": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        result = await db.conversations.insert_one(conversation)
        conversation["_id"] = result.inserted_id

    conversation_id = str(conversation["_id"])
    is_new = not request.conversation_id

    # Save user message to DB - use display_content for UI, not full message
    # This way when user reloads, they see short version, not full file content
    content_to_save = request.display_content if request.display_content else request.message
    
    user_message = {
        "role": "user",
        "content": content_to_save,
        "timestamp": datetime.utcnow(),
        "client_ip": client_ip,  # Store IP with each message
    }
    
    await db.conversations.update_one(
        {"_id": conversation["_id"]},
        {
            "$push": {"messages": user_message},
            "$set": {"updated_at": datetime.utcnow()},
        }
    )

    # ===== IP TRACKING =====
    await save_ip_message(
        client_ip=client_ip,
        user_id=user_id,
        conversation_id=conversation_id,
        message=content_to_save,
        user_agent=user_agent,
    )

    # Generate request_id and publish to Kafka
    # Send FULL message (with file content) to orchestrator for LLM processing
    request_id = str(uuid.uuid4())

    kafka_data = {
        "conversation_id": conversation_id,
        "message": request.message,  # Full message with file content
        "user_id": user_id,
        "generate_title": is_new,
    }

    await publish_chat_request(request_id, kafka_data)

    return ChatSendResponse(
        request_id=request_id,
        conversation_id=conversation_id,
    )


@router.get("/conversations", response_model=List[ConversationListItem])
async def list_conversations(
    user: dict = Depends(get_current_user_dep),
):
    """List all conversations for current user."""
    db = get_db()
    user_id = user["email"]

    cursor = db.conversations.find(
        {"user_id": user_id}
    ).sort("updated_at", -1).limit(50)

    conversations = []
    async for conv in cursor:
        conversations.append(ConversationListItem(
            id=str(conv["_id"]),
            title=conv.get("title", "New Conversation"),
            created_at=conv["created_at"],
            updated_at=conv["updated_at"],
            message_count=len(conv.get("messages", [])),
        ))

    return conversations


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    user: dict = Depends(get_current_user_dep),
):
    """Get conversation details with messages."""
    db = get_db()
    user_id = user["email"]

    try:
        conversation = await db.conversations.find_one({
            "_id": ObjectId(conversation_id),
            "user_id": user_id,
        })
    except Exception:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = []
    for msg in conversation.get("messages", []):
        messages.append(Message(
            role=msg["role"],
            content=msg["content"],
            timestamp=msg.get("timestamp", conversation["created_at"]),
        ))

    return ConversationDetail(
        id=str(conversation["_id"]),
        title=conversation.get("title", "New Conversation"),
        messages=messages,
        file_ids=[str(fid) for fid in conversation.get("file_ids", [])],
        created_at=conversation["created_at"],
        updated_at=conversation["updated_at"],
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user: dict = Depends(get_current_user_dep),
):
    """Delete a conversation."""
    db = get_db()
    user_id = user["email"]

    try:
        result = await db.conversations.delete_one({
            "_id": ObjectId(conversation_id),
            "user_id": user_id,
        })
    except Exception:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"message": "Conversation deleted"}
