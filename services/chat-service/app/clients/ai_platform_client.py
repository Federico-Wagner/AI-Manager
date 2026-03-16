import logging
from uuid import UUID

import httpx

from app.config.settings import settings

logger = logging.getLogger(__name__)

_FALLBACK_RESPONSE = "I'm sorry, the AI service is currently unavailable. Please try again later."


def _base_url() -> str:
    return settings.ai_platform_url


def generate_chat_response(
    chat_session_id: UUID,
    user_message: str,
    model: str,
    chat_summary: str | None,
    chat_last_messages: list[dict],
) -> str:
    """Call AI Platform /ai/generate-chat-response. Returns response text or fallback."""
    payload = {
        "chat_session_id": str(chat_session_id),
        "user_message": user_message,
        "model": model,
        "chat_summary": chat_summary,
        "chat_last_messages": chat_last_messages,
    }
    try:
        logger.info("Chat Service → AI request sent (session=%s model=%s)", chat_session_id, model)
        with httpx.Client(timeout=settings.ai_platform_timeout) as client:
            response = client.post(f"{_base_url()}/ai/generate-chat-response", json=payload)
            response.raise_for_status()
            return response.json()["response"]
    except Exception as e:
        logger.error("AI Platform call failed (session=%s): %s", chat_session_id, e)
        return _FALLBACK_RESPONSE


def generate_response(prompt: str, model: str) -> str:
    """Call AI Platform /ai/generate-response (no RAG). Returns response text or fallback."""
    payload = {"prompt": prompt, "model": model, "rag_retrieval": False}
    try:
        with httpx.Client(timeout=settings.ai_platform_timeout) as client:
            response = client.post(f"{_base_url()}/ai/generate-response", json=payload)
            response.raise_for_status()
            return response.json()["response"]
    except Exception as e:
        logger.error("AI Platform generate-response failed: %s", e)
        return ""


def ingest_document(
    document_id: UUID,
    chat_session_id: UUID,
    file_path: str,
    file_type: str,
) -> None:
    """Call AI Platform /documents/ingest-document (fire-and-forget)."""
    payload = {
        "document_id": str(document_id),
        "chat_session_id": str(chat_session_id),
        "file_path": file_path,
        "file_type": file_type,
    }
    try:
        with httpx.Client(timeout=10) as client:
            response = client.post(f"{_base_url()}/documents/ingest-document", json=payload)
            response.raise_for_status()
        logger.info("Document %s queued for ingestion on AI Platform", document_id)
    except Exception as e:
        logger.error("Failed to queue document %s for ingestion: %s", document_id, e)


def delete_document_chunks(document_id: UUID) -> None:
    """Call AI Platform DELETE /documents/{id}/chunks."""
    try:
        with httpx.Client(timeout=10) as client:
            response = client.delete(f"{_base_url()}/documents/{document_id}/chunks")
            response.raise_for_status()
        logger.info("Qdrant chunks deleted for document %s", document_id)
    except Exception as e:
        logger.error("Failed to delete Qdrant chunks for document %s: %s", document_id, e)
