import logging
from uuid import UUID
from app.config.settings import settings

from sqlalchemy import text
from sqlmodel import Session

from app.models.llm_call import LlmCall

logger = logging.getLogger(__name__)


def save_and_limit_persisted_llm_call(
    session: Session,
    chat_session_id: UUID,
    final_prompt: str,
    ai_response: str,
    model_name: str,
) -> None:
    """Persist an LLM call record (prompt + response) and trim table to last 10 rows."""
    call = LlmCall(
        chat_session_id=chat_session_id,
        final_prompt=final_prompt,
        ai_response=ai_response,
        model_name=model_name,
    )
    session.add(call)
    session.commit()

    session.execute(
        text(
            "DELETE FROM llm_calls WHERE id NOT IN "
            "(SELECT id FROM llm_calls ORDER BY created_at DESC LIMIT :limit)"
        ),
        {"limit": settings.ai_db_llm_call_max_calls_persisted},
    )
    session.commit()

    logger.debug(
        "LLM call stored — model=%s. Cleanup executed, remaining_calls<=%d",
        model_name,
        settings.ai_db_llm_call_max_calls_persisted,
    )
