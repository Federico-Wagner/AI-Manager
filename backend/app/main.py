import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat_controller import router as chat_router
from app.api.document_controller import router as document_router
from app.config.settings import settings
from app.database.connection import create_db_and_tables
from app.services import vector_store_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables and Qdrant collection on startup."""
    create_db_and_tables()
    vector_store_service.create_collection_if_not_exists()
    yield


app = FastAPI(
    title="AI Chat MVP",
    description="Chat with a local LLM via Ollama or an external model via OpenAI.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(document_router)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}
