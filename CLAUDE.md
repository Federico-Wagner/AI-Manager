# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

For full architecture, request flows, database schema, endpoints, and environment variables see:
- [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) — feature descriptions, memory system, RAG pipeline, logging examples
- [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) — file tree, endpoint reference, inter-service communication, Docker services table

## Running the Stack

```bash
# Build all images
docker compose --env-file docker-local.env -f docker-compose.yml build

# Start all services
docker compose --env-file docker-local.env -f docker-compose.yml up -d

# Pull Ollama model (first time)
docker exec -it claude-ai-lab-v1-ollama-1 ollama pull llama3
```

To run a single FastAPI service locally (from its directory):

```bash
python -m fastapi run app/main.py --host 0.0.0.0 --port 8000
```

Angular frontend (from `frontend/`):

```bash
npm start        # dev server on :4200
npm run build    # production build
```

## Key Conventions

- **Regular `def` endpoints** (not `async def`) throughout — FastAPI runs them in a threadpool. Async is used only where the framework requires it (lifespan, httpx in BFF).
- **SQLModel** for all ORM models (Chat Service and AI Platform Service).
- **`SessionDep` + `Annotated`** pattern for DB dependency injection.
- **`create_db_and_tables()`** called in lifespan startup — no Alembic migrations for MVP (Alembic is scaffolded at `database/migrations/` for future use).
- **CORS middleware lives in BFF only** — Chat Service has no CORS since it is internal-only.
- BFF uses a shared `httpx.AsyncClient` (created in lifespan, stored on `app.state`) for all upstream calls.
- `docker-local.env` is the single env file loaded by Docker Compose — it is not committed.
