from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Path

from app.database.connection import SessionDep
from app.schemas.chat_request import ChatRequest, CreateSessionRequest
from app.schemas.chat_response import ChatResponse, MessageResponse, SessionResponse
from app.services import chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/")
def send_message(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    session: SessionDep,
) -> ChatResponse:
    """Send a prompt and receive an AI response.

    Creates a new session automatically if chat_session_id is not provided.
    """
    return chat_service.process_chat(session=session, request=request, background_tasks=background_tasks)


@router.get("/sessions")
def list_sessions(session: SessionDep) -> list[SessionResponse]:
    """Return all chat sessions ordered by most recent first."""
    return chat_service.list_sessions(session)


@router.post("/sessions")
def create_session(request: CreateSessionRequest, session: SessionDep) -> SessionResponse:
    """Create a new chat session."""
    return chat_service.create_session(session=session, request=request)


@router.get("/sessions/{session_id}")
def get_session_messages(
    session_id: Annotated[UUID, Path(description="The chat session ID")],
    session: SessionDep,
) -> list[MessageResponse]:
    """Return all messages from a chat session in chronological order."""
    return chat_service.get_session_messages(session=session, chat_session_id=session_id)


@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: Annotated[UUID, Path(description="The chat session ID")],
    session: SessionDep,
) -> dict:
    """Delete a chat session and all associated data (messages, summary, documents, vector chunks)."""
    return chat_service.delete_session(session=session, session_id=session_id)
