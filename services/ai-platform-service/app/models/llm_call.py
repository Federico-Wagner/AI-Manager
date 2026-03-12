from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Index
from sqlmodel import Field, SQLModel


class LlmCall(SQLModel, table=True):
    __tablename__ = "llm_calls"
    __table_args__ = (
        Index("idx_llm_calls_created_at", "created_at"),
    )

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    chat_session_id: UUID  # no FK — chat_sessions lives in a separate DB
    final_prompt: str
    ai_response: str
    model_name: str = Field(max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
