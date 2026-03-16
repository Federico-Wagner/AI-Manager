import logging
from uuid import UUID

from fastapi import APIRouter, Request, UploadFile
from fastapi.responses import Response

from app.clients import chat_service_client as client
from app.schemas.document_schemas import DocumentResponse, DocumentUploadResponse

router = APIRouter(prefix="/sessions", tags=["documents"])
logger = logging.getLogger(__name__)


def _http(request: Request) -> object:
    return request.app.state.http_client


@router.post("/{session_id}/documents")
async def upload_document(
    session_id: UUID,
    file: UploadFile,
    request: Request,
) -> DocumentUploadResponse:
    logger.info(
        "BFF received POST /sessions/%s/documents — file=%s", session_id, file.filename
    )
    data = await client.upload_document(_http(request), session_id, file)
    logger.info("BFF returned upload response to frontend")
    return DocumentUploadResponse(**data)


@router.get("/{session_id}/documents")
async def list_documents(session_id: UUID, request: Request) -> list[DocumentResponse]:
    logger.info("BFF received GET /sessions/%s/documents", session_id)
    data = await client.list_documents(_http(request), session_id)
    return [DocumentResponse(**d) for d in data]


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(document_id: UUID, request: Request) -> Response:
    logger.info("BFF received DELETE /sessions/documents/%s", document_id)
    await client.delete_document(_http(request), document_id)
    return Response(status_code=204)
