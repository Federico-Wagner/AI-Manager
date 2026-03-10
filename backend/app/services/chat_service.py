import logging
from uuid import UUID

from fastapi import BackgroundTasks
from sqlmodel import Session

from app.config.settings import settings
from app.repositories import chat_repository, summary_repository
from app.router import model_router
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
        2. Fetch last N messages + existing summary for context (before saving current message)
        3. Persist user message
        4. Build context prompt (summary + recent history + user question)
        5. Route prompt to AI model
        6. Persist assistant response
        7. Schedule background summary check
        8. Return response with session ID
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

    # Step 4: build prompt with summary + recent history + user question
    context_prompt = memory_service.build_context_prompt(history, summary_text, request.prompt)

    # Step 5: call AI model
    ai_response = model_router.route(prompt=context_prompt, model=request.model)

    # Step 6: persist assistant message
    chat_repository.save_message(
        session=session,
        chat_session_id=chat_session.id,
        role="assistant",
        content=ai_response,
    )

    # Step 7: schedule summary check (runs after response is returned)
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
