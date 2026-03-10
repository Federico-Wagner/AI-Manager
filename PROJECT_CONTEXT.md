# claude-ai-lab-V1 — AI Chat MVP Context

## Descripción General

Local MVP AI chat application for experimentation and learning.
Allows chatting with either a **local LLM** (via Ollama) or an **external AI model** (via OpenAI API).
Runs fully locally, no authentication, focused on validating the architecture.

---

## Arquitectura

Simple unified backend (no BFF separation).

```
Frontend (Angular)
        ↓
Backend API (FastAPI)
        ↓
   Model Router
   ├── Local Model (Ollama / Llama 3)
   └── External Model (OpenAI / GPT-4o)
        ↓
PostgreSQL (chat persistence)
```

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
- **Responsibilities:** Handle chat requests, store messages, route prompts to AI models, return responses

### AI Models
| Type     | Runtime | Example Model |
|----------|---------|---------------|
| Local    | Ollama  | Llama 3       |
| External | OpenAI  | GPT-4o        |

### Database
- **PostgreSQL** — persists chat history

#### Tables

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
│   │   │   └── chat_controller.py      # FastAPI router — /chat endpoints
│   │   ├── services/
│   │   │   ├── chat_service.py         # Business logic orchestration
│   │   │   └── memory_service.py       # Prompt builder + background summary generation
│   │   ├── router/
│   │   │   └── model_router.py         # Routes prompts to Ollama or OpenAI
│   │   ├── clients/
│   │   │   ├── ollama_client.py        # httpx call to Ollama /api/generate
│   │   │   └── openai_client.py        # OpenAI SDK chat completion
│   │   ├── repositories/
│   │   │   ├── chat_repository.py      # All DB read/write operations
│   │   │   └── summary_repository.py   # get/upsert conversation_summaries
│   │   ├── models/
│   │   │   ├── chat_session.py         # SQLModel table: chat_sessions
│   │   │   ├── message.py              # SQLModel table: messages
│   │   │   └── conversation_summary.py # SQLModel table: conversation_summaries
│   │   ├── schemas/
│   │   │   ├── chat_request.py         # Pydantic request models
│   │   │   └── chat_response.py        # Pydantic response models
│   │   ├── database/
│   │   │   ├── connection.py           # Engine, SessionDep, create_all
│   │   │   └── base.py                 # Model imports for metadata registry
│   │   ├── config/
│   │   │   └── settings.py             # Pydantic BaseSettings (env vars)
│   │   └── main.py                     # FastAPI app + lifespan
│   ├── requirements.txt
│   └── Dockerfile
├── database/
│   ├── alembic.ini
│   └── migrations/
│       └── env.py                      # Alembic env (future migrations)
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/
│   │   │   │   └── chat/
│   │   │   │       ├── chat.component.ts   # Chat logic + API calls
│   │   │   │       ├── chat.component.html # Chat UI template
│   │   │   │       └── chat.component.css  # Bubble styles
│   │   │   ├── services/
│   │   │   │   └── chat.service.ts         # HttpClient wrapper for backend
│   │   │   ├── models/
│   │   │   │   ├── message.model.ts        # { role, content }
│   │   │   │   └── chat-response.model.ts  # ChatResponse, Session, MessageResponse
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

All services run locally via a single `docker-compose.yml`.

### Networks

Two Docker networks isolate traffic:

| Network    | Driver | Purpose                                                          |
|------------|--------|------------------------------------------------------------------|
| `public`   | bridge | Exposes frontend, backend, and postgres to the host machine      |
| `internal` | bridge (internal) | Service-to-service communication only — Ollama is **not** reachable from the host |

Ollama is intentionally **not port-mapped** to the host. Only `backend` can reach it via the `internal` network.

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
- [x] Session selector sidebar — list, switch, and start chat sessions from the UI

**Out of scope for MVP:** authentication, observability, advanced AI features.

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

Recent conversation:           ← only if history is non-empty
User: <message>
Assistant: <message>
...

User question:
<current prompt>
```

Config: `backend/app/config/settings.py` → `chat_context_window`, `summary_trigger_messages`, `summary_max_tokens`

---

## Session Selector (Frontend)

The Angular UI now includes a left sidebar for session management:

- Lists all sessions on load (ordered by most recent first)
- Highlights the active session
- Clicking a session loads its full message history
- **＋** button starts a new blank chat
- Sidebar auto-refreshes after each message is sent (captures auto-created sessions)

Component: `frontend/src/app/components/chat/chat.component.ts`
Service methods used: `getSessions()`, `getSessionMessages()` (previously defined but unused)

---

## Logging

Application-level logging is configured in `backend/app/main.py` via `logging.basicConfig(level=INFO)`.

Key log lines:
```
INFO  app.services.chat_service    Building context with N messages (window=8, session=<uuid>)
INFO  app.services.memory_service  Summary check: session=<uuid> unsummarized=N threshold=6
INFO  app.services.memory_service  Summary triggered: session=<uuid> (unsummarized=N, threshold=6)
INFO  app.services.memory_service  Summary updated: session=<uuid> summarized_count=N
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
