import logging
from uuid import UUID

from app.config.settings import settings
from app.services import vector_store_service
from app.services.document_ingestion_service import _get_model

logger = logging.getLogger(__name__)


def retrieve_relevant_chunks(query: str, chat_session_id: UUID) -> list[str]:
    """Embed the user query and return the most relevant document chunks from Qdrant.

    Returns an empty list if no documents exist for the session or if Qdrant
    is unavailable — the chat continues normally in both cases.
    """
    try:
        model = _get_model()
        query_embedding = model.encode(query).tolist()

        chunks = vector_store_service.search_chunks(
            query_vector=query_embedding,
            chat_session_id=chat_session_id,
            top_k=settings.rag_top_k,
        )

        # Apply character budget — prevents prompt explosion on large documents
        selected: list[str] = []
        total_chars = 0
        for chunk in chunks:
            if total_chars + len(chunk) > settings.rag_max_context_chars:
                break
            selected.append(chunk)
            total_chars += len(chunk)

        logger.info(
            "RAG retrieval: session=%s retrieved=%d selected=%d",
            chat_session_id,
            len(chunks),
            len(selected),
        )
        return selected

    except Exception as e:
        logger.warning("RAG retrieval failed (session=%s): %s", chat_session_id, e)
        return []
