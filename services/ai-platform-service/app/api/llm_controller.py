import logging

from fastapi import APIRouter

from app.database.connection import SessionDep
from app.repositories import llm_call_repository
from app.router import model_router
from app.schemas.ai_schemas import AiResponse, GenerateChatRequest, GenerateRequest
from app.services import rag_service
from app.services.prompt_builder import build_context_prompt

router = APIRouter(prefix="/ai", tags=["llm"])
logger = logging.getLogger(__name__)


@router.post("/generate-chat-response")
def generate_chat_response(
    request: GenerateChatRequest,
    db: SessionDep,
) -> AiResponse:
    """Full chat pipeline: RAG → prompt build → LLM call → log.

    Steps:
        1. Retrieve relevant RAG chunks for the user message
        2. Build 5-layer prompt (system + summary + RAG + history + question)
        3. Route to LLM
        4. Log prompt + response to llm_calls table
        5. Return response
    """
    # Step 1: RAG retrieval
    rag_chunks = rag_service.retrieve_relevant_chunks(
        query=request.user_message,
        chat_session_id=request.chat_session_id,
    )
    chunk_texts = [c["text"] for c in rag_chunks]

    # Step 2: Build prompt
    final_prompt = build_context_prompt(
        last_messages=request.chat_last_messages,
        summary_text=request.chat_summary,
        chunks=chunk_texts,
        current_prompt=request.user_message,
    )

    # Step 3: Call LLM
    logger.info("AI request sent — model=%s session=%s", request.model, request.chat_session_id)
    ai_response = model_router.route(prompt=final_prompt, model=request.model)
    logger.info("AI response generated — model=%s session=%s", request.model, request.chat_session_id)

    # Step 4: Log LLM call
    llm_call_repository.save_and_limit_persisted_llm_call(
        session=db,
        chat_session_id=request.chat_session_id,
        final_prompt=final_prompt,
        ai_response=ai_response,
        model_name=request.model,
    )

    return AiResponse(response=ai_response)


@router.post("/generate-response")
def generate_response(
    request: GenerateRequest,
    db: SessionDep,
) -> AiResponse:
    """Generic LLM call — no RAG, no logging. Used for summary generation."""
    logger.info("AI prompt executed — model=%s", request.model)
    ai_response = model_router.route(prompt=request.prompt, model=request.model)
    logger.info("AI response generated — model=%s", request.model)

    llm_call_repository.save_and_limit_persisted_llm_call(
        session=db,
        chat_session_id=None,
        final_prompt=request.prompt,
        ai_response=ai_response,
        model_name=request.model,
    )

    return AiResponse(response=ai_response)
