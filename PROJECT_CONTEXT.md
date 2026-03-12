# claude-ai-lab-V1 — AI Chat MVP Context

## Descripción General

Local MVP AI chat application for experimentation and learning.
Allows chatting with either a **local LLM** (via Ollama) or an **external AI model** (via OpenAI API).
Runs fully locally, no authentication, focused on validating the architecture.

---

## Arquitectura

Two-service architecture: Chat Service handles conversation management; AI Platform Service handles all AI/ML infrastructure.

```
Frontend (Angular, port 4200)
        ↓
Chat Service (FastAPI, port 8000)
   ├── chat_sessions, messages, conversation_summaries, documents (postgres-chat)
   └── ai_platform_client.py
        ↓  HTTP (internal Docker network)
AI Platform Service (FastAPI, port 8001)
   ├── RAG retrieval (rag_service → Qdrant)
   ├── Prompt builder (5-layer)
   ├── Model Router
   │   ├── Local Model (Ollama / Llama 3)
   │   └── External Model (OpenAI / GPT-4o)
   ├── LLM call logging (llm_calls, postgres-ai)
   └── Document ingestion (embed → Qdrant)
        ↓  status callback
Chat Service PATCH /internal/documents/{id}/status
```

See `PROJECT_STRUCTURE.md` for full file tree and endpoint reference.

---

## Technology Stack

### Frontend
- **Framework:** Angular
- **Responsibilities:** Chat UI, AI model selection (local or API), send prompts, display responses

### Backend
- **Framework:** FastAPI (Python 3.11)
- **ORM:** SQLModel (built on SQLAlchemy)
- **Migrations:** Alembic
- **HTTP Client:** httpx (Ollama calls)
- **Config:** pydantic-settings (BaseSettings)
- **Embeddings:** sentence-transformers (`all-MiniLM-L6-v2`, 384-dim)
- **Responsibilities:** Handle chat requests, store messages, route prompts to AI models, ingest documents, return responses

### AI Models
| Type     | Runtime | Example Model |
|----------|---------|---------------|
| Local    | Ollama  | Llama 3       |
| External | OpenAI  | GPT-4o        |

### Database
- **PostgreSQL** — persists chat history and document metadata
- **Qdrant** — vector database for document chunk embeddings

#### PostgreSQL Tables

`chat_sessions`
- id
- title
- created_at

`messages`
- id
- chat_session_id
- role (user | assistant)
- content
- created_at

`conversation_summaries`
- id
- chat_session_id (unique — one summary per session)
- summary_text
- summarized_message_count
- created_at
- updated_at

`documents`
- id
- chat_session_id
- file_name
- file_type (pdf | txt | md)
- file_size (bytes)
- storage_path (/data/uploads/{session_id}/{doc_id}/filename)
- status (uploaded | processing | processed | failed)
- created_at

`llm_calls`
- id
- chat_session_id
- final_prompt (full text sent to the model)
- model_name
- created_at
- **Retention policy:** only the 10 newest rows are kept globally (older rows auto-deleted after each insert)

#### Qdrant Collection

`documents_chunks`
- Vector size: 384 (all-MiniLM-L6-v2)
- Payload per point: `document_id`, `chat_session_id`, `chunk_index`, `text`

---

## Request Flow

```
User writes prompt in Angular UI
        ↓
POST /chat
        ↓
FastAPI Backend
        ↓
   Model Router
   ├── Ollama (local)
   └── OpenAI API (external)
        ↓
Response returned to frontend
        ↓
Message saved in PostgreSQL
```

### Model Selection Payload

```json
{ "prompt": "Explain Docker", "model": "local" }
// or
{ "prompt": "Explain Docker", "model": "openai" }
```

---

## Repository Structure (Monorepo)

```
claude-ai-lab-V1/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── chat_controller.py          # FastAPI router — /chat endpoints + DELETE session
│   │   │   └── document_controller.py      # FastAPI router — /sessions/{id}/documents endpoints
│   │   ├── services/
│   │   │   ├── chat_service.py             # Chat orchestration + delete_session()
│   │   │   ├── memory_service.py           # Prompt builder + background summary generation
│   │   │   ├── rag_service.py              # RAG retrieval: embed query → Qdrant search → chunk selection
│   │   │   ├── document_service.py         # Upload orchestration + delete (disk + Qdrant + DB)
│   │   │   ├── document_ingestion_service.py # Pipeline: extract → chunk → embed → store
│   │   │   └── vector_store_service.py     # Qdrant client wrapper
│   │   ├── router/
│   │   │   └── model_router.py             # Routes prompts to Ollama or OpenAI
│   │   ├── clients/
│   │   │   ├── ollama_client.py            # httpx call to Ollama /api/generate
│   │   │   └── openai_client.py            # OpenAI SDK chat completion
│   │   ├── repositories/
│   │   │   ├── chat_repository.py          # All DB read/write for chat
│   │   │   ├── summary_repository.py       # get/upsert conversation_summaries
│   │   │   ├── document_repository.py      # CRUD for documents table
│   │   │   └── llm_call_repository.py      # save_and_limit_persisted_llm_call() — inserts + auto-trims to 10 rows
│   │   ├── models/
│   │   │   ├── chat_session.py             # SQLModel table: chat_sessions
│   │   │   ├── message.py                  # SQLModel table: messages
│   │   │   ├── conversation_summary.py     # SQLModel table: conversation_summaries
│   │   │   ├── document.py                 # SQLModel table: documents
│   │   │   └── llm_call.py                 # SQLModel table: llm_calls
│   │   ├── schemas/
│   │   │   ├── chat_request.py             # Pydantic request models
│   │   │   ├── chat_response.py            # Pydantic response models
│   │   │   └── document_schemas.py         # DocumentUploadResponse, DocumentResponse
│   │   ├── database/
│   │   │   ├── connection.py               # Engine, SessionDep, create_all
│   │   │   └── base.py                     # Model imports for metadata registry
│   │   ├── config/
│   │   │   └── settings.py                 # Pydantic BaseSettings (env vars)
│   │   └── main.py                         # FastAPI app + lifespan + Qdrant init
│   ├── requirements.txt
│   └── Dockerfile
├── database/
│   ├── alembic.ini
│   └── migrations/
│       └── env.py                          # Alembic env (future migrations)
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/
│   │   │   │   ├── chat/
│   │   │   │   │   ├── chat.component.ts   # Chat logic + session delete
│   │   │   │   │   ├── chat.component.html # Chat UI + session delete button
│   │   │   │   │   └── chat.component.css  # Bubble styles + sidebar hover-reveal delete
│   │   │   │   └── documents-panel/
│   │   │   │       ├── documents-panel.component.ts   # Upload, list, delete documents
│   │   │   │       ├── documents-panel.component.html # Drop zone + document list
│   │   │   │       └── documents-panel.component.css  # Panel + status badge styles
│   │   │   ├── services/
│   │   │   │   ├── chat.service.ts         # HttpClient wrapper — chat + deleteSession()
│   │   │   │   └── document.service.ts     # HttpClient wrapper — documents API
│   │   │   ├── models/
│   │   │   │   ├── message.model.ts        # { role, content }
│   │   │   │   ├── chat-response.model.ts  # ChatResponse, Session, MessageResponse
│   │   │   │   └── document.model.ts       # Document, DocumentUploadResponse
│   │   │   ├── app.module.ts               # NgModule declarations
│   │   │   ├── app.component.ts/html/css   # Root shell with top bar
│   │   ├── environments/
│   │   │   ├── environment.ts              # apiBaseUrl for dev
│   │   │   └── environment.prod.ts         # apiBaseUrl for prod
│   │   ├── index.html
│   │   ├── main.ts
│   │   └── styles.css
│   ├── angular.json
│   ├── package.json
│   ├── tsconfig.json
│   ├── nginx.conf                          # SPA routing + cache headers
│   └── Dockerfile                          # Multi-stage: Node build + nginx serve
├── docker-compose.yml
├── docker-local.env                        # NOT committed — local secrets
└── .gitignore
```

---

## Local Infrastructure (Docker)

The entire application is **dockerized**. All services are managed via **Docker Compose**.

### Services

| Service    | Description                        | Port exposed | Networks           |
|------------|------------------------------------|--------------|--------------------|
| `frontend` | Angular app (served via Nginx)     | 4200         | public, internal   |
| `backend`  | FastAPI Python API                 | 8000         | public, internal   |
| `postgres` | PostgreSQL database                | 5432         | public, internal   |
| `ollama`   | Local LLM runtime                  | internal only| internal           |
| `qdrant`   | Vector database                    | 6333         | internal           |

All services run locally via a single `docker-compose.yml`.

### Volumes

| Volume         | Purpose                                    |
|----------------|--------------------------------------------|
| `postgres_data`| Persists PostgreSQL data                   |
| `ollama_data`  | Persists downloaded Ollama models          |
| `qdrant_data`  | Persists Qdrant vector index               |
| `uploads_data` | Persists uploaded files (`/data/uploads`)  |

### Networks

Two Docker networks isolate traffic:

| Network    | Driver | Purpose                                                          |
|------------|--------|------------------------------------------------------------------|
| `public`   | bridge | Exposes frontend, backend, and postgres to the host machine      |
| `internal` | bridge (internal) | Service-to-service only — Ollama and Qdrant are **not** reachable from the host |

Ollama and Qdrant are intentionally on the `internal` network only. Only `backend` can reach them.

---

## Environment Variables

All environment variables are defined in a single file:

```
docker-local.env
```

This file is loaded by `docker-compose.yml` and shared across services.
It is **not committed to version control** (add to `.gitignore`).

#### Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | — | PostgreSQL container config |
| `DB_USER` / `DB_PASSWORD` / `DB_HOST` / `DB_PORT` / `DB_NAME` | — | Backend DB connection |
| `OLLAMA_HOST` / `OLLAMA_PORT` / `OLLAMA_MODEL` | — | Ollama config |
| `OLLAMA_TIMEOUT` | `300` | Ollama request timeout in seconds |
| `OPENAI_API_KEY` | — | OpenAI API key (optional) |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model name |
| `CHAT_CONTEXT_WINDOW` | `8` | Number of recent messages included in each prompt |
| `SUMMARY_TRIGGER_MESSAGES` | `15` | Unsummarized messages needed to trigger a new summary |
| `SUMMARY_MAX_TOKENS` | `200` | Target token budget for generated summaries |
| `VECTOR_DB_URL` | `http://qdrant:6333` | Qdrant service URL |
| `UPLOADS_DIR` | `/data/uploads` | Host path inside backend container for uploaded files |
| `RAG_CHUNK_SIZE` | `300` | Approximate token size per text chunk |
| `RAG_CHUNK_OVERLAP` | `50` | Overlap between consecutive chunks (tokens) |
| `RAG_TOP_K` | `5` | Number of Qdrant chunks retrieved per query |
| `RAG_MAX_CONTEXT_CHARS` | `4000` | Character budget for RAG context injected into prompt |

---

## MVP Features

- [x] Chat UI (Angular 17 + NgModule + HttpClient)
- [x] FastAPI backend
- [x] Model routing (local / external)
- [x] Local LLM via Ollama
- [x] External AI via OpenAI
- [x] Chat history stored in PostgreSQL
- [x] Conversation memory — configurable context window injected into each prompt
- [x] Long-term memory — periodic LLM-generated summaries stored in DB, prepended to future prompts
- [x] Session selector sidebar — list, switch, start, and **delete** chat sessions from the UI
- [x] Document upload & RAG ingestion pipeline — upload PDF/TXT/MD per session, auto-chunk + embed + store in Qdrant
- [x] Documents panel — drag & drop upload, document list with status badges, per-document delete
- [x] RAG retrieval during chat (Stage 2) — query embedded, Qdrant searched per session, top chunks injected into prompt
- [x] LLM call logging — final prompt + model stored in `llm_calls` table, auto-retained to last 10 rows globally

**Out of scope for MVP:** authentication.

---

## Conversation Memory

The backend has a two-tier memory system:

### Short-Term Memory (Context Window)

Configurable via `CHAT_CONTEXT_WINDOW`. On each chat request, the last N messages are fetched from the DB and injected into the prompt.

### Long-Term Memory (Summarization)

When the number of unsummarized messages reaches `SUMMARY_TRIGGER_MESSAGES`, a background task calls the LLM to generate a compact summary of the older messages and stores it in `conversation_summaries`. On subsequent requests the summary is prepended to the prompt.

Summary generation runs as a `FastAPI BackgroundTask` — it never adds latency to chat responses. The task creates its own DB session from the shared `engine` (the request session is already closed).

Config: `SUMMARY_TRIGGER_MESSAGES`, `SUMMARY_MAX_TOKENS` in `docker-local.env`.
Implementation: `backend/app/services/memory_service.py` → `generate_summary_conditional()`.

### Prompt Format

```
System:
You are a helpful AI assistant.

Conversation summary:          ← only if a summary exists
<summary text>

Relevant document context:     ← only if RAG chunks retrieved
[Chunk 1]
<chunk text>
[Chunk 2]
<chunk text>

Recent conversation:           ← only if history is non-empty
User: <message>
Assistant: <message>
...

User question:
<current prompt>
```

Config: `backend/app/config/settings.py` → `chat_context_window`, `summary_trigger_messages`, `summary_max_tokens`, `rag_top_k`, `rag_max_context_chars`

---

## Session Selector (Frontend)

The Angular UI includes a left sidebar for session management:

- Lists all sessions on load (ordered by most recent first)
- Highlights the active session
- Clicking a session loads its full message history
- **＋** button starts a new blank chat
- **✕** button (hover-reveal) deletes a session with confirmation dialog — clears messages, documents, summary, and Qdrant chunks
- Sidebar auto-refreshes after each message is sent (captures auto-created sessions)

Component: `frontend/src/app/components/chat/chat.component.ts`
Service methods: `getSessions()`, `getSessionMessages()`, `deleteSession()`

---

## Document Upload & RAG Pipeline

Users can attach files to any chat session. Files are processed asynchronously into a vector database for future RAG retrieval.

### API Endpoints

#### Chat Service endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/sessions/{session_id}/documents` | Upload a file (multipart/form-data) |
| `GET` | `/sessions/{session_id}/documents` | List documents for a session |
| `DELETE` | `/sessions/documents/{document_id}` | Delete document (file + Qdrant + DB) |

#### AI Platform endpoints called by Chat Service

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/ai/generate-chat-response` | Full chat pipeline: RAG → prompt → LLM → log |
| `POST` | `/ai/generate-response` | Generic LLM call (no RAG, used for summaries) |
| `POST` | `/documents/ingest-document` | Background document ingestion |
| `DELETE` | `/documents/{id}/chunks` | Delete Qdrant chunks for a document |

### Ingestion Pipeline (BackgroundTask)

```
File upload (PDF / TXT / MD)
        ↓
Save to /data/uploads/{session_id}/{doc_id}/filename
        ↓
Persist Document record (status=uploaded)
        ↓
BackgroundTask: document_ingestion_service.process_document()
        ↓
  1. Extract text (pypdf / plain text)
  2. Chunk text (≈300 tokens, 50 token overlap)
  3. Embed chunks — SentenceTransformer("all-MiniLM-L6-v2") → 384-dim vectors
  4. Upsert points into Qdrant collection "documents_chunks"
  5. Update status → processed  (or failed on error)
```

The ingestion task runs after the upload response is returned — zero latency to the upload call.

### Document Status Values

| Status | Meaning |
|--------|---------|
| `uploaded` | File saved, ingestion not yet started |
| `processing` | Background task running |
| `processed` | Chunks stored in Qdrant — ready for RAG |
| `failed` | Ingestion error (logged, file kept) |

### Session Deletion Cascade

`DELETE /chat/sessions/{session_id}` removes in order:
1. Qdrant chunks for each document (`delete_document_chunks`)
2. Files on disk
3. Document DB records
4. Messages (bulk SQL DELETE)
5. Conversation summary
6. The session itself

### Frontend — Documents Panel

A 260px right-side panel (`DocumentsPanelComponent`) attached to each chat session:
- Drag & drop or file-picker upload (PDF, TXT, MD)
- Document list with color-coded status badges
- Per-document delete with confirmation
- Automatically reloads when the active session changes

Component: `frontend/src/app/components/documents-panel/`
Service: `frontend/src/app/services/document.service.ts`

---

## LLM Call Logging

After each LLM response, the backend stores a lightweight observability record in the `llm_calls` table. An immediate cleanup query trims the table to the **10 newest rows globally**, so storage footprint is fixed and tiny.

Fields stored per call: `chat_session_id`, `final_prompt` (the full assembled prompt), `ai_response` (the model's reply), `model_name`, `created_at`. Prompt and response are stored as a pair in the same row.

Implementation: `services/ai-platform-service/app/repositories/llm_call_repository.py` → `save_and_limit_persisted_llm_call()`.

Retention SQL (runs after every insert):
```sql
DELETE FROM llm_calls
WHERE id NOT IN (
    SELECT id FROM llm_calls ORDER BY created_at DESC LIMIT 10
);
```

---

## RAG Retrieval During Chat

When a user sends a message, the backend embeds the query using the same `all-MiniLM-L6-v2` model used during ingestion, queries Qdrant for the most relevant chunks belonging to the current session, and injects them into the LLM prompt between the conversation summary and the recent history.

### Retrieval Flow

```
User prompt
        ↓
rag_service.retrieve_relevant_chunks()
        ↓
  1. Embed query → 384-dim vector (shared _get_model() singleton)
  2. Qdrant search — filter by chat_session_id, limit=RAG_TOP_K
  3. Apply RAG_MAX_CONTEXT_CHARS character budget
  4. Return selected chunks ([] on any error — graceful degradation)
        ↓
Chunks injected as "Relevant document context" layer in prompt
        ↓
LLM responds with document-grounded answer
```

If Qdrant is unavailable or no documents have been uploaded for the session, `retrieve_relevant_chunks()` returns `[]` and the chat proceeds normally.

Config: `RAG_TOP_K`, `RAG_MAX_CONTEXT_CHARS` in `docker-local.env`.
Implementation: `services/ai-platform-service/app/services/rag_service.py`.

---

## Logging

Application-level logging is configured in each service's `main.py` via `logging.basicConfig(level=INFO)`.

**Chat Service logs:**
```
INFO  app.services.chat_service          Building context: N messages (window=N), summary=yes/no, session=<uuid>
INFO  app.clients.ai_platform_client     Chat Service → AI request sent (session=<uuid> model=local)
INFO  app.services.memory_service        Summary check: session=<uuid> unsummarized=N threshold=N
INFO  app.services.memory_service        Summary triggered / Summary updated
INFO  app.services.document_service      Document <uuid> uploaded: filename.pdf (N bytes)
INFO  app.api.internal_controller        Document <uuid> status updated → processed
INFO  app.services.chat_service          Session <uuid> deleted
```

**AI Platform Service logs:**
```
INFO  app.api.llm_controller                 AI request sent — model=local session=<uuid>
INFO  app.api.llm_controller                 AI response generated — model=local session=<uuid>
INFO  app.services.rag_service               RAG retrieval: session=<uuid> retrieved=N selected=N
INFO  app.services.document_ingestion_service  Processing document <uuid> (file.pdf)
INFO  app.services.document_ingestion_service  Document <uuid>: text extracted (N chars)
INFO  app.services.document_ingestion_service  Document <uuid>: N chunks generated
INFO  app.services.document_ingestion_service  Document <uuid>: embeddings stored in Qdrant
INFO  app.services.document_ingestion_service  Document <uuid>: status callback sent → processed
DEBUG app.repositories.llm_call_repository   LLM call stored — model=llama3. Cleanup executed, remaining_calls<=10
INFO  app.services.vector_store_service      Deleted Qdrant chunks for document <uuid>
```

---

## Historial de Cambios

| Fecha      | Descripción |
|------------|-------------|
| 2026-03-09 | Inicio del proyecto — contexto inicial definido |
| 2026-03-09 | Backend generado — FastAPI completo con SQLModel, Ollama, OpenAI, Docker Compose |
| 2026-03-09 | Frontend generado — Angular 17, ChatComponent, ChatService, nginx, Docker multi-stage |
| 2026-03-10 | Docker Compose refactorizado — redes public/internal, Ollama aislado sin exposición al host |
| 2026-03-10 | Memoria conversacional — CHAT_CONTEXT_WINDOW, get_last_messages(), prompt con historial |
| 2026-03-10 | Sidebar de sesiones en Angular — selector, carga de historial, botón nueva sesión |
| 2026-03-10 | Logging — logging.basicConfig en main.py, INFO en chat_service |
| 2026-03-10 | Memoria de largo plazo — summarization via BackgroundTask, tabla conversation_summaries, memory_service |
| 2026-03-10 | Timeout configurable para Ollama — OLLAMA_TIMEOUT env var, reemplaza hardcoded 120s |
| 2026-03-11 | RAG pipeline (Stage 1) — document upload, chunking, embeddings, Qdrant; tabla documents, docker qdrant service |
| 2026-03-11 | Documents panel Angular — drag & drop, status badges, delete por documento |
| 2026-03-11 | Delete chat session — cascade completo: Qdrant chunks + archivos + mensajes + summary + sesión |
| 2026-03-11 | RAG retrieval (Stage 2) — rag_service.py, search_chunks(), 5-layer prompt, RAG_TOP_K / RAG_MAX_CONTEXT_CHARS |
| 2026-03-11 | LLM call logging — llm_calls table, save_and_limit_persisted_llm_call(), 10-row global retention; fix qdrant client.search() → query_points() |
| 2026-03-12 | Service architecture refactor — monolith split into Chat Service (port 8000) + AI Platform Service (port 8001); two postgres instances; ai_platform_client.py; internal status callback; llm_calls adds ai_response column; PROJECT_STRUCTURE.md created |
| 2026-03-12 | AI Platform controller split — ai_controller.py split into llm_controller.py (prefix /ai) and document_controller.py (prefix /documents); chat-service client updated to new document routes; prompt_builder typo fix (last_mesages → last_messages) |
