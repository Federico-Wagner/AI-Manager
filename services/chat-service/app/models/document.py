from datetime import datetime
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    chat_session_id: UUID = Field(foreign_key="chat_sessions.id")
    file_name: str
    file_type: str      # "pdf" | "txt" | "md"
    file_size: int      # bytes
    storage_path: str   # /data/uploads/{session_id}/{doc_id}/filename
    status: str         # "uploaded" | "processing" | "processed" | "failed"
    created_at: datetime = Field(default_factory=datetime.utcnow)
