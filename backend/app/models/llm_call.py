from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class LlmCall(SQLModel, table=True):
    __tablename__ = "llm_calls"
    __table_args__ = (
        Index("idx_llm_calls_created_at", "created_at"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    chat_session_id: UUID = Field(foreign_key="chat_sessions.id")
    final_prompt: str
    model_name: str = Field(max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
