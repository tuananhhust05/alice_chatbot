from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserInDB(BaseModel):
    email: str
    name: str
    picture: Optional[str] = None
    google_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    picture: Optional[str] = None


class GoogleTokenPayload(BaseModel):
    credential: str
