import logging
from uuid import UUID

from sqlalchemy import text
from sqlmodel import Session

from app.models.llm_call import LlmCall

logger = logging.getLogger(__name__)

_MAX_CALLS = 10


def save_and_limit_persisted_llm_call(
    session: Session,
    chat_session_id: UUID,
    final_prompt: str,
    model_name: str,
) -> None:
    """Persist an LLM call record and trim the table to the last 10 rows globally."""
    call = LlmCall(
        chat_session_id=chat_session_id,
        final_prompt=final_prompt,
        model_name=model_name,
    )
    session.add(call)
    session.commit()

    session.execute(
        text(
            "DELETE FROM llm_calls WHERE id NOT IN "
            "(SELECT id FROM llm_calls ORDER BY created_at DESC LIMIT :limit)"
        ),
        {"limit": _MAX_CALLS},
    )
    session.commit()
