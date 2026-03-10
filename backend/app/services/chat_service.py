import logging
from uuid import UUID

from sqlmodel import Session

from app.config.settings import settings
from app.models.message import Message
from app.repositories import chat_repository
from app.router import model_router
from app.schemas.chat_request import ChatRequest, CreateSessionRequest
from app.schemas.chat_response import ChatResponse, MessageResponse, SessionResponse

logger = logging.getLogger(__name__)


def _build_context_prompt(history: list[Message], current_prompt: str) -> str:
    """Build a prompt string that includes conversation history as context."""
    parts = ["System:\nYou are a helpful AI assistant.\n"]
    if history:
        parts.append("Conversation history:\n")
        for msg in history:
            label = "User" if msg.role == "user" else "Assistant"
            parts.append(f"{label}: {msg.content}")
        parts.append("")  # blank line before user question
    parts.append(f"User question:\n{current_prompt}")
    return "\n".join(parts)


def process_chat(session: Session, request: ChatRequest) -> ChatResponse:
    """Orchestrate the full chat flow.

    Flow:
        1. Get or create chat session
        2. Fetch last N messages for context (before saving current message)
        3. Persist user message
        4. Build context prompt
        5. Route prompt to AI model
        6. Persist assistant response
        7. Return response with session ID
    """
    # Step 1: resolve session
    if request.chat_session_id:
        chat_session = chat_repository.get_session_by_id(session, request.chat_session_id)
    else:
        title = request.prompt[:60]
        chat_session = chat_repository.create_chat_session(session, title=title)

    # Step 2: fetch conversation history before saving current message
    context_window = settings.chat_context_window
    history = chat_repository.get_last_messages(
        session=session,
        chat_session_id=chat_session.id,
        limit=context_window,
    )
    logger.info(
        "Building context with %d messages (window=%d, session=%s)",
        len(history),
        context_window,
        chat_session.id,
    )

    # Step 3: persist user message
    chat_repository.save_message(
        session=session,
        chat_session_id=chat_session.id,
        role="user",
        content=request.prompt,
    )

    # Step 4: build prompt with conversation context
    context_prompt = _build_context_prompt(history, request.prompt)

    # Step 5: call AI model
    ai_response = model_router.route(prompt=context_prompt, model=request.model)

    # Step 6: persist assistant message
    chat_repository.save_message(
        session=session,
        chat_session_id=chat_session.id,
        role="assistant",
        content=ai_response,
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
