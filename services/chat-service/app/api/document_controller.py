from uuid import UUID

from fastapi import APIRouter, UploadFile

from app.database.connection import SessionDep
from app.repositories import document_repository
from app.schemas.document_schemas import DocumentResponse, DocumentUploadResponse
from app.services import document_service

router = APIRouter(prefix="/sessions", tags=["documents"])


@router.post("/{session_id}/documents")
def upload_document(
    session_id: UUID,
    file: UploadFile,
    session: SessionDep,
) -> DocumentUploadResponse:
    """Upload a file to a chat session and trigger background ingestion on AI Platform."""
    return document_service.handle_upload(
        session=session,
        session_id=session_id,
        file=file,
    )


@router.get("/{session_id}/documents")
def list_documents(session_id: UUID, session: SessionDep) -> list[DocumentResponse]:
    """List all documents for a chat session."""
    docs = document_repository.get_session_documents(session, session_id)
    return [
        DocumentResponse(
            id=d.id,
            file_name=d.file_name,
            file_type=d.file_type,
            file_size=d.file_size,
            status=d.status,
            created_at=d.created_at,
        )
        for d in docs
    ]


@router.delete("/documents/{document_id}")
def delete_document(document_id: UUID, session: SessionDep) -> dict:
    """Delete a document — removes file, Qdrant chunks (via AI Platform), and DB record."""
    return document_service.handle_delete(session=session, document_id=document_id)
