import logging
from uuid import UUID

from sentence_transformers import SentenceTransformer

from app.config.settings import settings
from app.services import vector_store_service

logger = logging.getLogger(__name__)

_embedding_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading embedding model all-MiniLM-L6-v2...")
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Embedding model loaded")
    return _embedding_model


def _extract_text(storage_path: str, file_type: str) -> str:
    """Extract raw text from a stored file."""
    if file_type in ("txt", "md"):
        with open(storage_path, encoding="utf-8") as f:
            return f.read()
    if file_type == "pdf":
        from pypdf import PdfReader
        reader = PdfReader(storage_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    raise ValueError(f"Unsupported file type: {file_type}")


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into overlapping chunks (1 token ≈ 4 chars)."""
    char_size = chunk_size * 4
    char_overlap = overlap * 4
    step = char_size - char_overlap

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + char_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += step

    return chunks


def warm_up_embedding_model() -> None:
    """Pre-load the embedding model so requests don't trigger a download mid-flight."""
    _get_model()


def _embed_chunks(chunks: list[str]) -> list[list[float]]:
    model = _get_model()
    vectors = model.encode(chunks, show_progress_bar=False)
    return [v.tolist() for v in vectors]


async def process_document(
    document_id: UUID,
    chat_session_id: UUID,
    file_path: str,
    file_type: str,
    chat_service_url: str,
) -> None:
    """Full ingestion pipeline. Calls back Chat Service on completion."""
    import httpx

    status = "failed"
    try:
        logger.info("Processing document %s (%s)", document_id, file_path)

        text = _extract_text(file_path, file_type)
        logger.info("Document %s: text extracted (%d chars)", document_id, len(text))

        chunks = _chunk_text(text, settings.rag_chunk_size, settings.rag_chunk_overlap)
        logger.info("Document %s: %d chunks generated", document_id, len(chunks))

        if not chunks:
            raise ValueError("No text content extracted from document")

        embeddings = _embed_chunks(chunks)

        vector_store_service.upsert_chunks(
            document_id=document_id,
            chat_session_id=chat_session_id,
            chunks=chunks,
            embeddings=embeddings,
        )
        logger.info("Document %s: embeddings stored in Qdrant", document_id)

        status = "processed"

    except Exception as e:
        logger.error("Document %s: ingestion failed — %s", document_id, e)

    # Callback to Chat Service to update document status
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.patch(
                f"{chat_service_url}/internal/documents/{document_id}/status",
                json={"status": status},
            )
        logger.info("Document %s: status callback sent → %s", document_id, status)
    except Exception as e:
        logger.warning("Document %s: status callback failed — %s", document_id, e)
