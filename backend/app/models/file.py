from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FileRecord(BaseModel):
    user_id: str
    conversation_id: str
    original_name: str
    file_type: str  # pdf, txt, csv
    file_path: str
    file_size: int
    chunk_count: int = 0
    weaviate_class: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FileUploadResponse(BaseModel):
    id: str
    original_name: str
    file_type: str
    file_size: int
    chunk_count: int
    conversation_id: str
