from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


# ── Requests ──────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    prompt: str
    model: str  # "local" | "openai"
    chat_session_id: UUID | None = None


class CreateSessionRequest(BaseModel):
    title: str = "New Chat"


# ── Responses ─────────────────────────────────────────────────────────────────

class ChatResponse(BaseModel):
    chat_session_id: UUID
    response: str


class SessionResponse(BaseModel):
    id: UUID
    title: str
    created_at: datetime


class MessageResponse(BaseModel):
    id: UUID
    chat_session_id: UUID
    role: str
    content: str
    created_at: datetime
