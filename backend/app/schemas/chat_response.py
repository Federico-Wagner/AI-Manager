from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ChatResponse(BaseModel):
    """Response returned after processing a chat prompt."""

    chat_session_id: UUID
    response: str


class SessionResponse(BaseModel):
    """Represents a chat session in API responses."""

    id: UUID
    title: str
    created_at: datetime


class MessageResponse(BaseModel):
    """Represents a message in API responses."""

    id: UUID
    chat_session_id: UUID
    role: str
    content: str
    created_at: datetime
