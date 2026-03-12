import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")

from app.api.document_controller import router as document_router
from app.api.llm_controller import router as llm_router
from app.database.connection import create_db_and_tables
from app.services import vector_store_service
from app.services.document_ingestion_service import warm_up_embedding_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables, Qdrant collection, and embedding model on startup."""
    create_db_and_tables()
    vector_store_service.create_collection_if_not_exists()
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, warm_up_embedding_model)
    yield


app = FastAPI(
    title="AI Platform Service",
    description="LLM execution, RAG retrieval, embeddings, and prompt logging.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(llm_router)
app.include_router(document_router)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    return {"status": "ok"}
