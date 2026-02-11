"""Models for IP tracking and message logging."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class IPMessage(BaseModel):
    """Track IP address for each message sent."""
    client_ip: str
    user_id: str
    conversation_id: str
    message_preview: str = ""  # First 200 chars of message
    user_agent: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class IPMessageInDB(IPMessage):
    """IP message as stored in database."""
    id: str


class IPStats(BaseModel):
    """IP statistics summary."""
    ip: str
    total_requests: int = 0
    total_messages: int = 0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    unique_users: int = 0
    is_blacklisted: bool = False


class IPBlacklistEntry(BaseModel):
    """IP blacklist entry."""
    ip: str
    reason: Optional[str] = ""
    blocked_at: datetime = Field(default_factory=datetime.utcnow)
    blocked_by: Optional[str] = "admin"
    expires_at: Optional[datetime] = None


class RateLimitConfig(BaseModel):
    """Rate limit configuration per endpoint type."""
    endpoint_type: str  # chat, file, auth, admin, default
    max_requests: int
    window_seconds: int = 60
