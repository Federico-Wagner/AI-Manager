import logging
from uuid import UUID

import httpx
from fastapi import HTTPException, UploadFile

from app.config.settings import settings

logger = logging.getLogger(__name__)


# ── Error handling ────────────────────────────────────────────────────────────

def _handle_error(e: Exception, context: str) -> None:
    """Map httpx transport errors to 503; propagate HTTP errors with original status."""
    if isinstance(e, httpx.ConnectError):
        logger.error("BFF → chat-service unreachable (%s): %s", context, e)
        raise HTTPException(status_code=503, detail="Chat service is currently unavailable.")
    if isinstance(e, httpx.TimeoutException):
        logger.error("BFF → chat-service timeout (%s): %s", context, e)
        raise HTTPException(status_code=503, detail="Chat service request timed out.")
    if isinstance(e, httpx.HTTPStatusError):
        logger.warning(
            "BFF → chat-service HTTP error (%s): status=%s body=%s",
            context, e.response.status_code, e.response.text,
        )
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    logger.error("BFF → chat-service unexpected error (%s): %s", context, e)
    raise HTTPException(status_code=502, detail="Unexpected error contacting chat service.")


def _timeout() -> int:
    return settings.chat_service_timeout


def _base() -> str:
    return settings.chat_service_url


# ── Chat endpoints ────────────────────────────────────────────────────────────

async def send_message(client: httpx.AsyncClient, payload: dict) -> dict:
    logger.info(
        "BFF → forwarding POST /chat/ (model=%s session=%s)",
        payload.get("model"), payload.get("chat_session_id"),
    )
    try:
        r = await client.post(f"{_base()}/chat/", json=payload, timeout=_timeout())
        r.raise_for_status()
        logger.info("BFF ← chat-service responded (session=%s)", payload.get("chat_session_id"))
        return r.json()
    except Exception as e:
        _handle_error(e, "send_message")


async def list_sessions(client: httpx.AsyncClient) -> list:
    logger.info("BFF → forwarding GET /chat/sessions")
    try:
        r = await client.get(f"{_base()}/chat/sessions", timeout=_timeout())
        r.raise_for_status()
        return r.json()
    except Exception as e:
        _handle_error(e, "list_sessions")


async def create_session(client: httpx.AsyncClient, payload: dict) -> dict:
    logger.info("BFF → forwarding POST /chat/sessions")
    try:
        r = await client.post(f"{_base()}/chat/sessions", json=payload, timeout=_timeout())
        r.raise_for_status()
        return r.json()
    except Exception as e:
        _handle_error(e, "create_session")


async def get_session_messages(client: httpx.AsyncClient, session_id: UUID) -> list:
    logger.info("BFF → forwarding GET /chat/sessions/%s", session_id)
    try:
        r = await client.get(f"{_base()}/chat/sessions/{session_id}", timeout=_timeout())
        r.raise_for_status()
        return r.json()
    except Exception as e:
        _handle_error(e, "get_session_messages")


async def delete_session(client: httpx.AsyncClient, session_id: UUID) -> None:
    logger.info("BFF → forwarding DELETE /chat/sessions/%s", session_id)
    try:
        r = await client.delete(f"{_base()}/chat/sessions/{session_id}", timeout=_timeout())
        r.raise_for_status()
        logger.info("BFF ← session %s deleted", session_id)
    except Exception as e:
        _handle_error(e, "delete_session")


# ── Document endpoints ────────────────────────────────────────────────────────

async def upload_document(
    client: httpx.AsyncClient,
    session_id: UUID,
    file: UploadFile,
) -> dict:
    logger.info(
        "BFF → forwarding POST /sessions/%s/documents (file=%s)",
        session_id, file.filename,
    )
    file_bytes = await file.read()
    try:
        r = await client.post(
            f"{_base()}/sessions/{session_id}/documents",
            files={"file": (file.filename, file_bytes, file.content_type)},
            timeout=_timeout(),
        )
        r.raise_for_status()
        logger.info("BFF ← document upload accepted for session %s", session_id)
        return r.json()
    except Exception as e:
        _handle_error(e, "upload_document")


async def list_documents(client: httpx.AsyncClient, session_id: UUID) -> list:
    logger.info("BFF → forwarding GET /sessions/%s/documents", session_id)
    try:
        r = await client.get(f"{_base()}/sessions/{session_id}/documents", timeout=_timeout())
        r.raise_for_status()
        return r.json()
    except Exception as e:
        _handle_error(e, "list_documents")


async def delete_document(client: httpx.AsyncClient, document_id: UUID) -> None:
    logger.info("BFF → forwarding DELETE /sessions/documents/%s", document_id)
    try:
        r = await client.delete(f"{_base()}/sessions/documents/{document_id}", timeout=_timeout())
        r.raise_for_status()
        logger.info("BFF ← document %s deleted", document_id)
    except Exception as e:
        _handle_error(e, "delete_document")
