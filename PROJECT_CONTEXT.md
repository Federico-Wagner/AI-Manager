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
- **Framework:** FastAPI (Python)
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
ai-chat-mvp/
├── frontend/
│   └── angular-app/
├── backend/
│   └── app/
│       ├── api/
│       │   └── chat_controller.py
│       ├── services/
│       │   └── chat_service.py
│       ├── router/
│       │   └── model_router.py
│       ├── clients/
│       │   ├── ollama_client.py
│       │   └── openai_client.py
│       ├── repositories/
│       │   └── chat_repository.py
│       ├── models/
│       │   ├── chat_session.py
│       │   └── message.py
│       ├── database/
│       │   └── connection.py
│       └── main.py
├── database/
│   └── migrations/
└── docker-compose.yml
```

### Frontend Structure (Angular)

```
src/app/
├── components/
│   └── chat/
│       ├── chat.component.ts
│       └── chat.component.html
├── services/
│   └── chat.service.ts
└── models/
    └── message.ts
```

---

## Local Infrastructure (Docker)

The entire application is **dockerized**. All services are managed via **Docker Compose**.

### Services

| Service    | Description                        | Port  |
|------------|------------------------------------|-------|
| `frontend` | Angular app (served via Nginx)     | 4200  |
| `backend`  | FastAPI Python API                 | 8000  |
| `postgres` | PostgreSQL database                | 5432  |
| `ollama`   | Local LLM runtime                  | 11434 |

All services run locally via a single `docker-compose.yml`.

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

# Frontend
API_BASE_URL=http://localhost:8000
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

- [x] Chat UI (Angular)
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
