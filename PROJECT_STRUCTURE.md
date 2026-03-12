# Project Structure — claude-ai-lab-V1

## Architecture Overview

```
Browser / Frontend (Angular, port 4200)
           │
           ▼
  ┌─────────────────┐
  │  Chat Service   │  port 8000  — conversation management
  │  (FastAPI)      │
  └────────┬────────┘
           │ HTTP (internal Docker network)
           ▼
  ┌──────────────────────┐
  │  AI Platform Service │  port 8001  — LLM, RAG, embeddings
  │  (FastAPI)           │
  └──┬───────────────────┘
     │              │
     ▼              ▼
 Qdrant          Ollama / OpenAI
 (vectors)       (LLM)
```

---

## Repository Layout

```
claude-ai-lab-V1/
│
├── services/
│   │
│   ├── chat-service/               # Conversation management
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app/
│   │       ├── main.py
│   │       ├── api/
│   │       │   ├── chat_controller.py      # POST/GET /chat, /sessions
│   │       │   ├── document_controller.py  # POST/GET/DELETE /sessions/{id}/documents
│   │       │   └── internal_controller.py  # PATCH /internal/documents/{id}/status
│   │       ├── clients/
│   │       │   └── ai_platform_client.py   # HTTP client → AI Platform Service
│   │       ├── config/
│   │       │   └── settings.py             # chat_db_*, ai_platform_url, conversation settings
│   │       ├── database/
│   │       │   ├── base.py                 # model imports for SQLModel metadata
│   │       │   └── connection.py           # engine, SessionDep
│   │       ├── models/
│   │       │   ├── chat_session.py         # chat_sessions table
│   │       │   ├── message.py              # messages table
│   │       │   ├── document.py             # documents table
│   │       │   └── conversation_summary.py # conversation_summaries table
│   │       ├── repositories/
│   │       │   ├── chat_repository.py
│   │       │   ├── document_repository.py
│   │       │   └── summary_repository.py
│   │       ├── schemas/
│   │       │   ├── chat_request.py
│   │       │   ├── chat_response.py
│   │       │   └── document_schemas.py
│   │       └── services/
│   │           ├── chat_service.py         # orchestrates chat flow
│   │           ├── memory_service.py       # summary generation (calls AI Platform)
│   │           └── document_service.py     # file save + AI Platform ingest trigger
│   │
│   └── ai-platform-service/        # AI infrastructure
│       ├── Dockerfile
│       ├── requirements.txt
│       └── app/
│           ├── main.py
│           ├── api/
│           │   ├── llm_controller.py       # POST /ai/generate-chat-response, /ai/generate-response
│           │   └── document_controller.py  # POST /documents/ingest-document, DELETE /documents/{id}/chunks
│           ├── clients/
│           │   ├── ollama_client.py
│           │   └── openai_client.py
│           ├── config/
│           │   └── settings.py             # ai_db_*, ollama, openai, qdrant, rag settings
│           ├── database/
│           │   ├── base.py
│           │   └── connection.py
│           ├── models/
│           │   └── llm_call.py             # llm_calls table (prompt + response pair)
│           ├── repositories/
│           │   └── llm_call_repository.py  # save + 10-row retention
│           ├── router/
│           │   └── model_router.py         # routes to ollama/openai
│           ├── schemas/
│           │   └── ai_schemas.py
│           └── services/
│               ├── rag_service.py          # embed query + Qdrant search
│               ├── document_ingestion_service.py  # extract → chunk → embed → upsert
│               ├── vector_store_service.py # Qdrant client wrapper
│               └── prompt_builder.py       # 5-layer prompt construction
│
├── frontend/                       # Angular app
├── docker-compose.yml
├── docker-local.env                # local secrets (not committed)
├── PROJECT_CONTEXT.md
└── PROJECT_STRUCTURE.md            # this file
```

---

## Service Responsibilities

### Chat Service (port 8000)

**Owns:** `chat_sessions`, `messages`, `conversation_summaries`, `documents` tables in **postgres-chat**

**Does:**
- Receive messages from frontend
- Persist user/assistant messages
- Manage chat sessions and document metadata
- Call AI Platform for LLM responses and document ingestion
- Trigger summary generation (via AI Platform)
- Return AI responses to frontend

**Does NOT:** talk to Qdrant, Ollama, or OpenAI directly

---

### AI Platform Service (port 8001, internal only)

**Owns:** `llm_calls` table in **postgres-ai** + Qdrant vector DB

**Does:**
- Embed user queries and search Qdrant
- Build 5-layer prompt (system + summary + RAG chunks + history + question)
- Route prompts to Ollama or OpenAI
- Log every prompt+response pair to `llm_calls` (last 10 retained)
- Process document uploads (extract text → chunk → embed → store in Qdrant)
- Callback to Chat Service when ingestion completes

---

## AI Platform Endpoints

### LLM (`llm_controller.py`, prefix `/ai`)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/ai/generate-chat-response` | Full chat pipeline: RAG → prompt → LLM → log |
| `POST` | `/ai/generate-response` | Generic LLM call (no RAG, used for summaries) |

### Documents (`document_controller.py`, prefix `/documents`)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/documents/ingest-document` | Background document ingestion |
| `DELETE` | `/documents/{id}/chunks` | Delete Qdrant chunks for a document |

---

## Chat Service Internal Endpoint

| Method | Path | Description |
|--------|------|-------------|
| `PATCH` | `/internal/documents/{id}/status` | Called by AI Platform after ingestion completes |

---

## Database Ownership

| Database | Service | Tables |
|----------|---------|--------|
| `postgres-chat` | Chat Service | `chat_sessions`, `messages`, `conversation_summaries`, `documents` |
| `postgres-ai` | AI Platform Service | `llm_calls` |

---

## Inter-Service Communication

```
Chat Service ──────────────────────────────────► AI Platform
  generate_chat_response()       POST /ai/generate-chat-response
  generate_response()            POST /ai/generate-response
  ingest_document()              POST /documents/ingest-document
  delete_document_chunks()       DELETE /documents/{id}/chunks

AI Platform ───────────────────────────────────► Chat Service
  (after ingestion completes)    PATCH /internal/documents/{id}/status
```

Error handling: if AI Platform is unreachable, Chat Service returns a fallback message and logs the error. The chat system never crashes due to AI Platform unavailability.

---

## Environment Variables

### Chat Service

| Variable | Description |
|----------|-------------|
| `CHAT_DB_NAME/HOST/PORT/USER/PASSWORD` | postgres-chat connection |
| `AI_PLATFORM_URL` | `http://ai-platform-service:8001` |
| `AI_PLATFORM_TIMEOUT` | HTTP timeout for AI calls (seconds) |
| `CHAT_CONTEXT_WINDOW` | Messages to include in prompt history |
| `SUMMARY_TRIGGER_MESSAGES` | Unsummarized messages before summary runs |
| `SUMMARY_MAX_TOKENS` | Max tokens in generated summary |
| `UPLOADS_DIR` | `/data/uploads` |
| `CORS_ORIGINS` | Allowed frontend origins |

### AI Platform Service

| Variable | Description |
|----------|-------------|
| `AI_DB_NAME/HOST/PORT/USER/PASSWORD` | postgres-ai connection |
| `CHAT_SERVICE_URL` | `http://chat-service:8000` |
| `OLLAMA_HOST/PORT/MODEL/TIMEOUT` | Ollama configuration |
| `OPENAI_API_KEY/MODEL` | OpenAI configuration |
| `VECTOR_DB_URL` | `http://qdrant:6333` |
| `UPLOADS_DIR` | `/data/uploads` (shared volume) |
| `RAG_CHUNK_SIZE` | Chunk size in tokens (approx) |
| `RAG_CHUNK_OVERLAP` | Overlap between chunks in tokens |
| `RAG_TOP_K` | Max chunks retrieved per query |
| `RAG_MAX_CONTEXT_CHARS` | Character budget for RAG context in prompt |

---

## Docker Services

| Service | Image | Port | Network |
|---------|-------|------|---------|
| `frontend` | custom | 4200 | public + internal |
| `chat-service` | custom | 8000 | public + internal |
| `ai-platform-service` | custom | 8001 | internal only |
| `postgres-chat` | postgres:15 | 5432 | internal |
| `postgres-ai` | postgres:15 | 5433→5432 | internal |
| `ollama` | ollama/ollama | 11434 (exposed) | internal |
| `qdrant` | qdrant/qdrant | 6333 | internal + public (dashboard) |

Shared volume `uploads_data` is mounted at `/data/uploads` on both `chat-service` and `ai-platform-service`.
