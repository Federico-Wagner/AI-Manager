"""Internal endpoints — called by AI Platform Service only, not exposed to frontend."""
import logging
from uuid import UUID

from pydantic import BaseModel
from fastapi import APIRouter

from app.database.connection import SessionDep
from app.repositories import document_repository

router = APIRouter(prefix="/internal", tags=["internal"])
logger = logging.getLogger(__name__)


class StatusUpdate(BaseModel):
    status: str  # "processed" | "failed"


@router.patch("/documents/{document_id}/status")
def update_document_status(
    document_id: UUID,
    body: StatusUpdate,
    session: SessionDep,
) -> dict:
    """Called by AI Platform Service to update document ingestion status."""
    document_repository.update_status(session, document_id, body.status)
    logger.info("Document %s status updated → %s", document_id, body.status)
    return {"document_id": str(document_id), "status": body.status}
