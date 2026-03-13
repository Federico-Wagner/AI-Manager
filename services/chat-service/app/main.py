import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")

from app.api.chat_controller import router as chat_router
from app.api.document_controller import router as document_router
from app.api.internal_controller import router as internal_router
from app.database.connection import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables on startup."""
    create_db_and_tables()
    yield


app = FastAPI(
    title="Chat Service",
    description="Conversation management — sessions, messages, summaries, and documents.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(chat_router)
app.include_router(document_router)
app.include_router(internal_router)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}
