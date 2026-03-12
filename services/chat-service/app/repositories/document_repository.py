from uuid import UUID

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models.document import Document


def save_document(
    session: Session,
    chat_session_id: UUID,
    file_name: str,
    file_type: str,
    file_size: int,
    storage_path: str,
) -> Document:
    doc = Document(
        chat_session_id=chat_session_id,
        file_name=file_name,
        file_type=file_type,
        file_size=file_size,
        storage_path=storage_path,
        status="uploaded",
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return doc


def get_document(session: Session, document_id: UUID) -> Document:
    doc = session.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


def get_session_documents(session: Session, chat_session_id: UUID) -> list[Document]:
    return list(
        session.exec(
            select(Document)
            .where(Document.chat_session_id == chat_session_id)
            .order_by(Document.created_at)
        ).all()
    )


def update_status(session: Session, document_id: UUID, status: str) -> Document:
    doc = get_document(session, document_id)
    doc.status = status
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return doc


def delete_document(session: Session, document_id: UUID) -> None:
    doc = get_document(session, document_id)
    session.delete(doc)
    session.commit()
