from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models.chat_session import ChatSession
from app.models.message import Message


def get_all_sessions(session: Session) -> list[ChatSession]:
    """Return all chat sessions ordered by creation date descending."""
    return list(
        session.exec(
            select(ChatSession).order_by(ChatSession.created_at.desc())
        ).all()
    )


def get_session_by_id(session: Session, chat_session_id: UUID) -> ChatSession:
    """Return a chat session by ID, raising 404 if not found."""
    chat_session = session.get(ChatSession, chat_session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return chat_session


def get_session_messages(session: Session, chat_session_id: UUID) -> list[Message]:
    """Return all messages for a session ordered by creation date ascending."""
    return list(
        session.exec(
            select(Message)
            .where(Message.chat_session_id == chat_session_id)
            .order_by(Message.created_at)
        ).all()
    )


def get_last_messages(session: Session, chat_session_id: UUID, limit: int) -> list[Message]:
    """Return the last `limit` messages for a session in chronological order."""
    rows = list(
        session.exec(
            select(Message)
            .where(Message.chat_session_id == chat_session_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        ).all()
    )
    return list(reversed(rows))


def create_chat_session(session: Session, title: str = "New Chat") -> ChatSession:
    """Create and persist a new chat session."""
    chat_session = ChatSession(title=title)
    session.add(chat_session)
    session.commit()
    session.refresh(chat_session)
    return chat_session


def save_message(
    session: Session,
    chat_session_id: UUID,
    role: str,
    content: str,
) -> Message:
    """Persist a message to the database."""
    message = Message(
        chat_session_id=chat_session_id,
        role=role,
        content=content,
    )
    session.add(message)
    session.commit()
    session.refresh(message)
    return message
