import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Path, Request
from fastapi.responses import Response

from app.clients import chat_service_client as client
from app.schemas.chat_schemas import (
    ChatRequest,
    ChatResponse,
    CreateSessionRequest,
    MessageResponse,
    SessionResponse,
)

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


def _http(request: Request) -> object:
    return request.app.state.http_client


@router.post("/")
async def send_message(body: ChatRequest, request: Request) -> ChatResponse:
    logger.info("BFF received POST /chat/ — model=%s", body.model)
    data = await client.send_message(_http(request), body.model_dump(mode="json"))
    logger.info("BFF returned response to frontend")
    return ChatResponse(**data)


@router.get("/sessions")
async def list_sessions(request: Request) -> list[SessionResponse]:
    logger.info("BFF received GET /chat/sessions")
    data = await client.list_sessions(_http(request))
    return [SessionResponse(**s) for s in data]


@router.post("/sessions")
async def create_session(body: CreateSessionRequest, request: Request) -> SessionResponse:
    logger.info("BFF received POST /chat/sessions")
    data = await client.create_session(_http(request), body.model_dump())
    return SessionResponse(**data)


@router.get("/sessions/{session_id}")
async def get_session_messages(
    session_id: Annotated[UUID, Path(description="Chat session ID")],
    request: Request,
) -> list[MessageResponse]:
    logger.info("BFF received GET /chat/sessions/%s", session_id)
    data = await client.get_session_messages(_http(request), session_id)
    return [MessageResponse(**m) for m in data]


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: Annotated[UUID, Path(description="Chat session ID")],
    request: Request,
) -> Response:
    logger.info("BFF received DELETE /chat/sessions/%s", session_id)
    await client.delete_session(_http(request), session_id)
    return Response(status_code=204)
