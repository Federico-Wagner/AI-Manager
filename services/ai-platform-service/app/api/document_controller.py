import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks

from app.config.settings import settings
from app.schemas.ai_schemas import IngestDocumentRequest
from app.services import document_ingestion_service

router = APIRouter(prefix="/documents", tags=["documents"])
logger = logging.getLogger(__name__)


@router.post("/ingest-document")
def ingest_document(
    request: IngestDocumentRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    """Schedule background document ingestion (embed + store in Qdrant)."""
    background_tasks.add_task(
        document_ingestion_service.process_document,
        document_id=request.document_id,
        chat_session_id=request.chat_session_id,
        file_path=request.file_path,
        file_type=request.file_type,
        chat_service_url=settings.chat_service_url,
    )
    logger.info("Document %s queued for ingestion", request.document_id)
    return {"status": "processing"}


@router.delete("/{document_id}/chunks")
def delete_document_chunks(document_id: UUID) -> dict:
    """Remove all Qdrant vector points for a document."""
    from app.services import vector_store_service
    vector_store_service.delete_document_chunks(document_id)
    return {"message": "deleted"}
