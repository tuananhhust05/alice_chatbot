from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Conversation(BaseModel):
    user_id: str
    title: str = "New Conversation"
    messages: List[Message] = []
    file_ids: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    message: str                           # Full message with file content (for LLM)
    display_content: Optional[str] = None  # Short display version (for UI)
    conversation_id: Optional[str] = None


# POST /api/chat/send → returns request_id for polling
class ChatSendResponse(BaseModel):
    request_id: str
    conversation_id: str


# GET /api/stream?request_id=xxx → streaming response
class StreamResponse(BaseModel):
    status: str  # "processing" | "streaming" | "completed" | "error"
    reply: Optional[str] = None
    title: Optional[str] = None
    finished: int = 0  # 0 = not done, 1 = done
    error: Optional[str] = None


class ConversationListItem(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class ConversationDetail(BaseModel):
    id: str
    title: str
    messages: List[Message]
    file_ids: List[str] = []
    created_at: datetime
    updated_at: datetime
