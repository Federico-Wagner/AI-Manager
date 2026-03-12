import logging
from uuid import UUID

from app.config.settings import settings
from app.services import vector_store_service
from app.services.document_ingestion_service import _get_model

logger = logging.getLogger(__name__)


def retrieve_relevant_chunks(query: str, chat_session_id: UUID) -> list[dict]:
    """Embed the user query and return the most relevant document chunks from Qdrant.

    Each chunk is a dict with keys: chunk_id, score, text.
    Returns an empty list if no documents exist for the session or if Qdrant
    is unavailable — the chat continues normally in both cases.
    """
    model = _get_model()
    query_embedding = model.encode(query).tolist()

    chunks = vector_store_service.search_chunks(
        query_vector=query_embedding,
        chat_session_id=chat_session_id,
        top_k=settings.rag_top_k,
    )

    # Apply character budget — prevents prompt explosion on large documents
    selected: list[dict] = []
    total_chars = 0
    for chunk in chunks:
        if total_chars + len(chunk["text"]) > settings.rag_max_context_chars_on_prompt:
            break
        selected.append(chunk)
        total_chars += len(chunk["text"])

    logger.info(
        "RAG retrieval: session=%s retrieved=%d selected=%d",
        chat_session_id,
        len(chunks),
        len(selected),
    )
    return selected
