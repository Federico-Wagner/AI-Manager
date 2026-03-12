import logging
import os
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile
from sqlmodel import Session

from app.clients import ai_platform_client
from app.config.settings import settings
from app.repositories import document_repository
from app.schemas.document_schemas import DocumentUploadResponse

logger = logging.getLogger(__name__)

SUPPORTED_TYPES = {"pdf", "txt", "md"}


def handle_upload(
    session: Session,
    session_id: UUID,
    file: UploadFile,
) -> DocumentUploadResponse:
    """Save uploaded file to disk, persist metadata, and trigger AI Platform ingestion."""
    # Validate file type
    file_name = file.filename or "upload"
    extension = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    if extension not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{extension}'. Allowed: {', '.join(sorted(SUPPORTED_TYPES))}",
        )

    # Determine storage path and save file
    document_id = uuid4()
    upload_dir = os.path.join(settings.uploads_dir, str(session_id), str(document_id))
    os.makedirs(upload_dir, exist_ok=True)
    storage_path = os.path.join(upload_dir, file_name)

    contents = file.file.read()
    with open(storage_path, "wb") as f:
        f.write(contents)

    logger.info("Document %s uploaded: %s (%d bytes)", document_id, file_name, len(contents))

    # Persist metadata
    doc = document_repository.save_document(
        session=session,
        chat_session_id=session_id,
        file_name=file_name,
        file_type=extension,
        file_size=len(contents),
        storage_path=storage_path,
    )

    # Trigger AI Platform ingestion (async, best-effort)
    ai_platform_client.ingest_document(
        document_id=doc.id,
        chat_session_id=session_id,
        file_path=storage_path,
        file_type=extension,
    )

    return DocumentUploadResponse(document_id=doc.id, status=doc.status)


def handle_delete(session: Session, document_id: UUID) -> dict:
    """Delete document chunks from Qdrant (via AI Platform), file from disk, and record from DB."""
    doc = document_repository.get_document(session, document_id)

    # Remove from vector store via AI Platform
    ai_platform_client.delete_document_chunks(document_id)

    # Remove file from disk (best-effort)
    try:
        if os.path.exists(doc.storage_path):
            os.remove(doc.storage_path)
        parent = os.path.dirname(doc.storage_path)
        if os.path.isdir(parent) and not os.listdir(parent):
            os.rmdir(parent)
    except OSError as e:
        logger.warning("Could not remove file for document %s: %s", document_id, e)

    # Remove DB record
    document_repository.delete_document(session, document_id)

    logger.info("Document %s deleted", document_id)
    return {"message": "deleted"}
