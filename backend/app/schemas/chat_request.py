from uuid import UUID

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Request body for sending a chat prompt."""

    prompt: str
    model: str  # "local" or "openai"
    chat_session_id: UUID | None = None


class CreateSessionRequest(BaseModel):
    """Request body for creating a new chat session."""

    title: str = "New Chat"
