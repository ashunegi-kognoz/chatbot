from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class ChatRequest(BaseModel):
    query: str
    top_k: int = 5
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    message_id: str
    conversation_id: str
    response_id: str

class FileUploadResponse(BaseModel):
    message: str
    file_id: str
    chunks_added: int

class Conversation(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime

class Message(BaseModel):
    id: str
    conversation_id: str
    role: str  # "user" or "assistant"
    content: str
    response_id: Optional[str] = None  # OpenAI response ID for threading
    parent_message_id: Optional[str] = None
    created_at: datetime