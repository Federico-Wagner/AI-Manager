from uuid import UUID

from pydantic import BaseModel


class MessageItem(BaseModel):
    role: str   # "user" | "assistant"
    content: str


class GenerateChatRequest(BaseModel):
    """Full chat generation: RAG + prompt build + LLM call."""
    chat_session_id: UUID
    user_message: str
    model: str  # "local" | "openai"
    chat_summary: str | None = None
    chat_last_messages: list[MessageItem] = []


class GenerateRequest(BaseModel):
    """Generic LLM call (e.g. summary generation). No RAG."""
    prompt: str
    model: str  # "local" | "openai"
    rag_retrieval: bool = False


class IngestDocumentRequest(BaseModel):
    """Trigger background ingestion for an already-uploaded file."""
    document_id: UUID
    chat_session_id: UUID
    file_path: str
    file_type: str  # "pdf" | "txt" | "md"


class AiResponse(BaseModel):
    response: str
