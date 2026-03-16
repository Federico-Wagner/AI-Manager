from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel


class Message(SQLModel, table=True):
    """Represents a single message within a chat session."""

    __tablename__ = "messages"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    chat_session_id: UUID = Field(foreign_key="chat_sessions.id")
    role: str  # "user" | "assistant"
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    chat_session: "ChatSession" = Relationship(back_populates="messages")
