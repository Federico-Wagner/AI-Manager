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

#### Tables (MVP)

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
│   │   │   └── chat_service.py         # Business logic orchestration
│   │   ├── router/
│   │   │   └── model_router.py         # Routes prompts to Ollama or OpenAI
│   │   ├── clients/
│   │   │   ├── ollama_client.py        # httpx call to Ollama /api/generate
│   │   │   └── openai_client.py        # OpenAI SDK chat completion
│   │   ├── repositories/
│   │   │   └── chat_repository.py      # All DB read/write operations
│   │   ├── models/
│   │   │   ├── chat_session.py         # SQLModel table: chat_sessions
│   │   │   └── message.py              # SQLModel table: messages
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

### Environment Variables

All environment variables are defined in a single file:

```
docker-local.env
```

This file is loaded by `docker-compose.yml` and shared across services.
It is **not committed to version control** (add to `.gitignore`).

#### Example variables

```env
# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=ai_chat

# Backend
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/ai_chat
OPENAI_API_KEY=sk-...
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_HOST=ollama
OLLAMA_PORT=11434
```

---

### Docker Commands

#### Build all images

```bash
docker-compose build
```

#### Build a specific service image

```bash
docker-compose build frontend
docker-compose build backend
```

#### Start all containers

```bash
docker-compose up
```

#### Start in detached mode (background)

```bash
docker-compose up -d
```

#### Start and rebuild images before starting

```bash
docker-compose up --build
```

#### Start a specific service

```bash
docker-compose up backend
docker-compose up ollama
```

#### Stop all containers

```bash
docker-compose down
```

#### Stop and remove volumes (wipes DB data)

```bash
docker-compose down -v
```

#### View running containers

```bash
docker-compose ps
```

#### View logs

```bash
docker-compose logs -f            # all services
docker-compose logs -f backend    # specific service
```

#### Execute command inside a container

```bash
docker-compose exec backend bash
docker-compose exec postgres psql -U postgres
```

---

## MVP Features

- [x] Chat UI (Angular 17 + NgModule + HttpClient)
- [x] FastAPI backend
- [x] Model routing (local / external)
- [x] Local LLM via Ollama
- [x] External AI via OpenAI
- [x] Chat history stored in PostgreSQL

**Out of scope for MVP:** authentication, observability, advanced AI features.

---

## Historial de Cambios

| Fecha      | Descripción |
|------------|-------------|
| 2026-03-09 | Inicio del proyecto — contexto inicial definido |
| 2026-03-09 | Backend generado — FastAPI completo con SQLModel, Ollama, OpenAI, Docker Compose |
| 2026-03-09 | Frontend generado — Angular 17, ChatComponent, ChatService, nginx, Docker multi-stage |
| 2026-03-10 | Docker Compose refactorizado — redes public/internal, Ollama aislado sin exposición al host |
