import logging
from uuid import UUID, uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, PointStruct, VectorParams

from app.config.settings import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "documents_chunks" #TODO reubicate in .env file
VECTOR_SIZE = 384       #TODO reubicate in .env file


def _get_client() -> QdrantClient:
    return QdrantClient(url=settings.vector_db_url)


def create_collection_if_not_exists() -> None:
    """Create the Qdrant collection on startup if it doesn't exist yet."""
    client = _get_client()
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )
        logger.info("Qdrant collection '%s' created", COLLECTION_NAME)
    else:
        logger.info("Qdrant collection '%s' already exists", COLLECTION_NAME)


def upsert_chunks(
    document_id: UUID,
    chat_session_id: UUID,
    chunks: list[str],
    embeddings: list[list[float]],
) -> None:
    """Store embedded chunks in Qdrant with document metadata as payload."""
    client = _get_client()
    points = [
        PointStruct(
            id=str(uuid4()),
            vector=embeddings[i],
            payload={
                "document_id": str(document_id),
                "chat_session_id": str(chat_session_id),
                "chunk_index": i,
                "text": chunks[i],
            },
        )
        for i in range(len(chunks))
    ]
    client.upsert(collection_name=COLLECTION_NAME, points=points)


def search_chunks(
    query_vector: list[float],
    chat_session_id: UUID,
    top_k: int,
) -> list[dict]:
    """Return the top-k most relevant chunks for this session with metadata."""
    client = _get_client()
    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="chat_session_id",
                    match=MatchValue(value=str(chat_session_id)),
                )
            ]
        ),
        limit=top_k,
    )
    return [
        {"chunk_id": str(hit.id), "score": round(hit.score, 4), "text": hit.payload["text"]}
        for hit in response.points
        if hit.payload
    ]


def delete_document_chunks(document_id: UUID) -> None:
    """Remove all Qdrant points belonging to a document."""
    client = _get_client()
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=str(document_id)),
                )
            ]
        ),
    )
    logger.info("Deleted Qdrant chunks for document %s", document_id)
