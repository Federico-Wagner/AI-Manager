from uuid import UUID

from sqlmodel import Session

from app.repositories import chat_repository
from app.router import model_router
from app.schemas.chat_request import ChatRequest, CreateSessionRequest
from app.schemas.chat_response import ChatResponse, MessageResponse, SessionResponse


def process_chat(session: Session, request: ChatRequest) -> ChatResponse:
    """Orchestrate the full chat flow.

    Flow:
        1. Get or create chat session
        2. Persist user message
        3. Route prompt to AI model
        4. Persist assistant response
        5. Return response with session ID
    """
    # Step 1: resolve session
    if request.chat_session_id:
        chat_session = chat_repository.get_session_by_id(session, request.chat_session_id)
    else:
        title = request.prompt[:60]
        chat_session = chat_repository.create_chat_session(session, title=title)

    # Step 2: persist user message
    chat_repository.save_message(
        session=session,
        chat_session_id=chat_session.id,
        role="user",
        content=request.prompt,
    )

    # Step 3: call AI model
    ai_response = model_router.route(prompt=request.prompt, model=request.model)

    # Step 4: persist assistant message
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
