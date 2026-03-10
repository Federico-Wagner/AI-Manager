from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class ConversationSummary(SQLModel, table=True):
    """Stores a running summary of older messages for a chat session."""

    __tablename__ = "conversation_summaries"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    chat_session_id: UUID = Field(foreign_key="chat_sessions.id", unique=True)
    summary_text: str
    summarized_message_count: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
