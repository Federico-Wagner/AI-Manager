import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")

from app.config.settings import settings
from app.routers.chat_router import router as chat_router
from app.routers.document_router import router as document_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient()
    logger.info("BFF httpx.AsyncClient created — downstream: %s", settings.chat_service_url)
    yield
    await app.state.http_client.aclose()
    logger.info("BFF httpx.AsyncClient closed.")


app = FastAPI(
    title="BFF Service",
    description="Backend For Frontend — proxies all public API traffic to Chat Service.",
    version="1.0.0",
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
async def health_check() -> dict:
    return {"status": "ok"}
