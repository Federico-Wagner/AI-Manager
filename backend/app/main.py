from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.chat_controller import router as chat_router
from app.database.connection import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables on startup."""
    create_db_and_tables()
    yield


app = FastAPI(
    title="AI Chat MVP",
    description="Chat with a local LLM via Ollama or an external model via OpenAI.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(chat_router)


@app.get("/health", tags=["health"])
def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}
