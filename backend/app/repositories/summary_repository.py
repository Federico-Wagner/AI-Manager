from datetime import datetime
from uuid import UUID

from sqlmodel import Session, select

from app.models.conversation_summary import ConversationSummary


def get_summary(session: Session, chat_session_id: UUID) -> ConversationSummary | None:
    """Return the summary for a chat session, or None if it doesn't exist yet."""
    return session.exec(
        select(ConversationSummary).where(
            ConversationSummary.chat_session_id == chat_session_id
        )
    ).first()


def upsert_summary(
    session: Session,
    chat_session_id: UUID,
    summary_text: str,
    message_count: int,
) -> ConversationSummary:
    """Create or update the summary for a chat session."""
    existing = get_summary(session, chat_session_id)
    if existing:
        existing.summary_text = summary_text
        existing.summarized_message_count = message_count
        existing.updated_at = datetime.utcnow()
        session.add(existing)
    else:
        existing = ConversationSummary(
            chat_session_id=chat_session_id,
            summary_text=summary_text,
            summarized_message_count=message_count,
        )
        session.add(existing)
    session.commit()
    session.refresh(existing)
    return existing
