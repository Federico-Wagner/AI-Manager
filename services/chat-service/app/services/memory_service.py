import logging
from uuid import UUID

from sqlmodel import Session

from app.clients import ai_platform_client
from app.config.settings import settings
from app.models.message import Message
from app.repositories import chat_repository, summary_repository

logger = logging.getLogger(__name__)


def _build_summary_prompt(
    existing_summary: str | None,
    new_messages: list[Message],
) -> str:
    """Build the prompt used to generate or update a conversation summary."""
    parts = ["System:\nYou summarize conversations.\n"]

    if existing_summary:
        parts.append(f"Current summary:\n{existing_summary}\n")

    parts.append("New conversation messages:\n")
    for msg in new_messages:
        label = "User" if msg.role == "user" else "Assistant"
        parts.append(f"{label}: {msg.content}")

    parts.append(
        f"\nInstructions:\n"
        f"Update the summary to include the new information.\n"
        f"Keep it concise and under {settings.summary_max_tokens} tokens.\n"
        f"Focus on the user's goals and important context.\n"
        f"Return only the updated summary."
    )
    return "\n".join(parts)


def generate_summary_conditional(chat_session_id: UUID, model: str) -> None:
    """Check if a summary update is needed and run it. Designed to run as a BackgroundTask.

    Creates its own DB session since the request session is already closed by the time
    background tasks execute.
    """
    from app.database.connection import engine  # local import avoids circular deps at module load

    with Session(engine) as db_session:
        all_messages = chat_repository.get_session_messages(db_session, chat_session_id)
        total = len(all_messages)

        existing = summary_repository.get_summary(db_session, chat_session_id)
        summarized = existing.summarized_message_count if existing else 0
        unsummarized = total - summarized

        logger.info(
            "Summary check: session=%s unsummarized=%d threshold=%d",
            chat_session_id,
            unsummarized,
            settings.summary_trigger_messages,
        )

        if unsummarized < settings.summary_trigger_messages:
            return

        logger.info(
            "Summary triggered: session=%s (unsummarized=%d, threshold=%d)",
            chat_session_id,
            unsummarized,
            settings.summary_trigger_messages,
        )

        messages_to_summarize = all_messages[summarized:]
        summary_prompt = _build_summary_prompt(
            existing_summary=existing.summary_text if existing else None,
            new_messages=messages_to_summarize,
        )

        new_summary = ai_platform_client.generate_response(prompt=summary_prompt, model=model)

        if new_summary:
            summary_repository.upsert_summary(
                session=db_session,
                chat_session_id=chat_session_id,
                summary_text=new_summary,
                message_count=total,
            )

            logger.info(
                "Summary updated: session=%s summarized_count=%d",
                chat_session_id,
                total,
            )
