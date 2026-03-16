import logging
import os
from uuid import UUID

from fastapi import BackgroundTasks
from sqlmodel import Session, delete as sql_delete

from app.clients import ai_platform_client
from app.config.settings import settings
from app.models.chat_session import ChatSession
from app.models.message import Message
from app.repositories import chat_repository, document_repository, summary_repository
from app.schemas.chat_request import ChatRequest, CreateSessionRequest
from app.schemas.chat_response import ChatResponse, MessageResponse, SessionResponse
from app.services import memory_service

logger = logging.getLogger(__name__)


def process_chat(
    session: Session,
    request: ChatRequest,
    background_tasks: BackgroundTasks,
) -> ChatResponse:
    """Orchestrate the full chat flow.

    Flow:
        1. Get or create chat session
        2. Fetch last N messages + existing summary for context
        3. Persist user message
        4. Call AI Platform Service (RAG + prompt build + LLM)
        5. Persist assistant response
        6. Schedule background summary check
        7. Return response with session ID
    """
    # Step 1: resolve session
    if request.chat_session_id:
        chat_session = chat_repository.get_session_by_id(session, request.chat_session_id)
    else:
        title = request.prompt[:60]
        chat_session = chat_repository.create_chat_session(session, title=title)

    # Step 2: fetch context before saving current message
    context_window = settings.chat_context_window
    history = chat_repository.get_last_messages(
        session=session,
        chat_session_id=chat_session.id,
        limit=context_window,
    )
    existing_summary = summary_repository.get_summary(session, chat_session.id)
    summary_text = existing_summary.summary_text if existing_summary else None

    logger.info(
        "Building context: %d messages (window=%d), summary=%s, session=%s",
        len(history),
        context_window,
        "yes" if summary_text else "no",
        chat_session.id,
    )

    # Step 3: persist user message
    chat_repository.save_message(
        session=session,
        chat_session_id=chat_session.id,
        role="user",
        content=request.prompt,
    )

    # Step 4: call AI Platform Service
    history_payload = [{"role": m.role, "content": m.content} for m in history]
    ai_response = ai_platform_client.generate_chat_response(
        chat_session_id=chat_session.id,
        user_message=request.prompt,
        model=request.model,
        chat_summary=summary_text,
        chat_last_messages=history_payload,
    )

    # Step 5: persist assistant message
    chat_repository.save_message(
        session=session,
        chat_session_id=chat_session.id,
        role="assistant",
        content=ai_response,
    )

    # Step 6: schedule summary check (runs after response is returned)
    background_tasks.add_task(
        memory_service.generate_summary_conditional,
        chat_session_id=chat_session.id,
        model=request.model,
    )

    return ChatResponse(chat_session_id=chat_session.id, response=ai_response)


def list_sessions(session: Session) -> list[SessionResponse]:
    """Return all chat sessions."""
    sessions = chat_repository.get_all_sessions(session)
    return [
        SessionResponse(id=s.id, title=s.title, created_at=s.created_at)
        for s in sessions
    ]


def create_session(session: Session, request: CreateSessionRequest) -> SessionResponse:
    """Create a new named chat session."""
    chat_session = chat_repository.create_chat_session(session, title=request.title)
    return SessionResponse(
        id=chat_session.id,
        title=chat_session.title,
        created_at=chat_session.created_at,
    )


def get_session_messages(session: Session, chat_session_id: UUID) -> list[MessageResponse]:
    """Return all messages in a chat session."""
    chat_repository.get_session_by_id(session, chat_session_id)  # raises 404 if missing
    messages = chat_repository.get_session_messages(session, chat_session_id)
    return [
        MessageResponse(
            id=m.id,
            chat_session_id=m.chat_session_id,
            role=m.role,
            content=m.content,
            created_at=m.created_at,
        )
        for m in messages
    ]


def delete_session(session: Session, session_id: UUID) -> dict:
    """Delete a chat session and all associated data.

    Deletion order:
        1. All documents — Qdrant chunks (via AI Platform) + file on disk + DB record
        2. All messages (bulk delete)
        3. Conversation summary (if exists)
        4. The session itself
    """
    chat_repository.get_session_by_id(session, session_id)  # raises 404 if missing

    # Delete documents (Qdrant chunks via AI Platform + files + DB records)
    docs = document_repository.get_session_documents(session, session_id)
    for doc in docs:
        ai_platform_client.delete_document_chunks(doc.id)
        _delete_doc_files(doc.storage_path)
        document_repository.delete_document(session, doc.id)

    # Bulk delete messages
    session.exec(sql_delete(Message).where(Message.chat_session_id == session_id))

    # Delete summary if present
    existing_summary = summary_repository.get_summary(session, session_id)
    if existing_summary:
        session.delete(existing_summary)

    # Delete session
    chat_session = session.get(ChatSession, session_id)
    session.delete(chat_session)
    session.commit()

    logger.info("Session %s deleted", session_id)
    return {"message": "deleted"}


def _delete_doc_files(storage_path: str) -> None:
    """Remove a document file and its parent directory (best-effort)."""
    try:
        if os.path.exists(storage_path):
            os.remove(storage_path)
        parent = os.path.dirname(storage_path)
        if os.path.isdir(parent) and not os.listdir(parent):
            os.rmdir(parent)
    except OSError as e:
        logger.warning("Could not remove file %s: %s", storage_path, e)
