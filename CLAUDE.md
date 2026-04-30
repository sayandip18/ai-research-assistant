# CLAUDE.md — AI Research Assistant

This file is the primary reference for Claude Code when working in this repository.
Read it fully before making any changes. When in doubt, follow the patterns already
established in the codebase rather than inventing new ones.

---

## Project overview

A production-grade AI Research Assistant backend built with FastAPI, PostgreSQL,
pgvector, Redis, and OpenAI APIs. The system combines RAG (Retrieval-Augmented
Generation), a tool-calling agent loop, async document ingestion, and real-time
SSE streaming. The frontend is a React/TypeScript SPA.

---

## Repository layout

```
.
├── backend/
│   ├── main.py                  # FastAPI app factory, lifespan, router registration
│   ├── config.py                # Pydantic Settings — all env vars live here
│   ├── dependencies.py          # Shared FastAPI Depends (db, redis, current_user)
│   ├── alembic/                 # DB migrations — never edit schema directly
│   │   ├── env.py
│   │   └── versions/
│   ├── auth/
│   │   ├── router.py            # POST /auth/register, /login, /refresh, /logout
│   │   ├── service.py           # Password hashing, JWT creation/validation
│   │   ├── repository.py        # DB queries for users
│   │   ├── models.py            # SQLAlchemy User model
│   │   └── schemas.py           # Pydantic request/response schemas
│   ├── chat/
│   │   ├── router.py            # POST /chat, GET /chat/{id}/history
│   │   ├── service.py           # Conversation CRUD, message assembly
│   │   ├── repository.py
│   │   ├── models.py            # Conversation, Message models
│   │   └── schemas.py
│   ├── agents/
│   │   ├── router.py            # POST /agents/run (non-streaming)
│   │   ├── orchestrator.py      # ReAct loop, tool dispatch, step limiting
│   │   ├── prompts.py           # All system prompt templates
│   │   └── schemas.py
│   ├── rag/
│   │   ├── pipeline.py          # Hybrid retrieval + RRF merge + context assembly
│   │   ├── rewriter.py          # Query rewriting and decomposition
│   │   ├── citations.py         # Citation ID injection and extraction
│   │   └── schemas.py
│   ├── embeddings/
│   │   ├── service.py           # embed_query(), embed_documents()
│   │   └── cache.py             # Redis-backed embedding cache
│   ├── ingestion/
│   │   ├── parsers.py           # PDF, DOCX, TXT, MD text extractors
│   │   ├── chunker.py           # Recursive character splitter
│   │   └── pipeline.py         # Orchestrates parse → chunk → embed → store
│   ├── vectorstore/
│   │   ├── repository.py        # similarity_search(), keyword_search(), upsert()
│   │   └── models.py            # DocumentChunk SQLAlchemy model
│   ├── streaming/
│   │   ├── router.py            # GET /chat/{session_id}/stream  (SSE)
│   │   ├── handler.py           # Async generator, event formatting
│   │   └── events.py            # Typed event dataclasses
│   ├── tools/
│   │   ├── base.py              # BaseTool ABC with name/description/parameters
│   │   ├── retrieve.py          # RetrieveDocumentsTool
│   │   ├── web_search.py        # WebSearchTool (Tavily)
│   │   ├── calculator.py        # CalculatorTool
│   │   ├── summarise.py         # SummariseTool
│   │   ├── notes.py             # SaveNoteTool, RecallNoteTool
│   │   └── registry.py          # Tool registry — add new tools here
│   ├── memory/
│   │   ├── service.py           # Short-term (Redis) + long-term (DB) memory
│   │   ├── repository.py        # agent_memory table queries
│   │   ├── models.py            # AgentMemory SQLAlchemy model
│   │   └── summariser.py        # Sliding window conversation summariser
│   ├── documents/
│   │   ├── router.py            # POST /documents/upload, GET /documents/{id}
│   │   ├── service.py           # Orchestrates upload → enqueue
│   │   ├── repository.py
│   │   ├── models.py            # Document SQLAlchemy model
│   │   └── schemas.py
│   ├── workers/
│   │   ├── celery_app.py        # Celery app factory and config
│   │   └── tasks.py             # ingest_document() task definition
│   └── common/
│       ├── db.py                # Async SQLAlchemy engine and session factory
│       ├── redis.py             # Redis client factory
│       ├── storage.py           # S3/MinIO client wrappers
│       ├── exceptions.py        # Custom exception classes
│       ├── logging.py           # structlog configuration
│       └── metrics.py           # Prometheus counters and histograms
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat/            # ChatPanel, MessageBubble, StreamingMessage
│   │   │   ├── Sidebar/         # ConversationList, WorkspaceTree
│   │   │   ├── Documents/       # UploadZone, DocumentCard, StatusBadge
│   │   │   └── Citations/       # CitationPanel, CitationFootnote
│   │   ├── hooks/
│   │   │   ├── useSSE.ts        # EventSource management, event routing
│   │   │   ├── useChat.ts       # Message state, send, optimistic updates
│   │   │   └── useDocuments.ts  # Upload, poll status, list
│   │   ├── api/                 # Typed fetch wrappers for every endpoint
│   │   ├── stores/              # Zustand stores (auth, chat, documents)
│   │   └── types/               # Shared TypeScript interfaces
│   ├── vite.config.ts
│   └── tsconfig.json
├── tests/
│   ├── unit/                    # Service and utility unit tests (no DB)
│   ├── integration/             # Tests that hit the real DB/Redis in Docker
│   └── conftest.py              # pytest fixtures, test DB setup
├── docker-compose.yml
├── docker-compose.test.yml
├── Dockerfile.api
├── Dockerfile.worker
├── .env.example
├── alembic.ini
└── pyproject.toml
```

---

## Environment and tooling

### Python

- Python 3.12+. Use `pyproject.toml` with `[project]` + `[tool.uv]` — do not use
  `requirements.txt` or `setup.py`.
- Package manager: `uv`. Install deps with `uv add <pkg>`, not `pip install`.
- Virtual env is at `.venv/` — always activate before running scripts locally.
- Formatter: `ruff format`. Linter: `ruff check`. Type checker: `pyright`.
  Run all three before committing: `make lint`.

### Node

- Node 20+. Package manager: `pnpm`. All frontend commands run from `frontend/`.
- `pnpm dev` — Vite dev server on port 5173 with proxy to `localhost:8000`.
- `pnpm build` — production build to `frontend/dist/`.
- TypeScript strict mode is on. Do not use `any` — use `unknown` and narrow it.

### Docker

- `docker compose up` — starts `api`, `worker`, `db`, `redis`.
- `docker compose up --build` — rebuilds images after dependency changes.
- `docker compose run --rm api alembic upgrade head` — run migrations.
- The `api` and `worker` containers share the same image (`Dockerfile.api`).
  The `worker` overrides CMD to `celery -A workers.celery_app worker`.

---

## Running the stack locally

```bash
# 1. Copy env and fill in secrets
cp .env.example .env

# 2. Start all services
docker compose up -d

# 3. Run migrations
docker compose run --rm api alembic upgrade head

# 4. Frontend dev server
cd frontend && pnpm install && pnpm dev
```

The API is at `http://localhost:8000`. Interactive docs at `/docs`.

---

## Configuration

All configuration lives in `backend/config.py` as a `pydantic_settings.BaseSettings`
subclass. Every value is read from environment variables. Never hardcode secrets or
URLs in application code — always go through `settings`.

```python
# Correct
from backend.config import settings
client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

# Wrong
client = openai.AsyncOpenAI(api_key="sk-...")
```

Key settings groups:

| Prefix                          | Purpose                                                    |
| ------------------------------- | ---------------------------------------------------------- |
| `DATABASE_URL`                  | asyncpg DSN for SQLAlchemy                                 |
| `REDIS_URL`                     | Redis connection string                                    |
| `OPENAI_API_KEY`                | OpenAI API key                                             |
| `OPENAI_EMBEDDING_MODEL`        | Default: `text-embedding-3-small`                          |
| `OPENAI_CHAT_MODEL`             | Default: `gpt-4o`                                          |
| `JWT_SECRET`                    | HS256 signing key — must be ≥32 chars                      |
| `JWT_ACCESS_EXPIRE_MINUTES`     | Default: 15                                                |
| `JWT_REFRESH_EXPIRE_DAYS`       | Default: 7                                                 |
| `S3_BUCKET` / `S3_ENDPOINT_URL` | Object storage (MinIO locally)                             |
| `CELERY_BROKER_URL`             | Redis DSN for Celery broker                                |
| `TAVILY_API_KEY`                | Web search tool                                            |
| `MAX_AGENT_STEPS`               | Safety cap on ReAct loop iterations (default: 10)          |
| `CHUNK_SIZE`                    | Tokens per chunk (default: 512)                            |
| `CHUNK_OVERLAP`                 | Overlap between chunks (default: 64)                       |
| `RETRIEVAL_TOP_K`               | Chunks returned per query (default: 8)                     |
| `EMBEDDING_CACHE_TTL`           | Redis TTL for cached embeddings in seconds (default: 3600) |

---

## Database

### Migrations

Use Alembic for **all** schema changes. Never run raw DDL against the database.

```bash
# Create a new migration (after changing a SQLAlchemy model)
docker compose run --rm api alembic revision --autogenerate -m "add_token_usage_table"

# Apply
docker compose run --rm api alembic upgrade head

# Roll back one step
docker compose run --rm api alembic downgrade -1
```

Migration files live in `alembic/versions/`. Each file must be reviewed before
committing — autogenerate is a starting point, not a final answer.

### Session management

Use the async session dependency from `backend/dependencies.py`:

```python
from backend.dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession

@router.get("/example")
async def example(db: AsyncSession = Depends(get_db)):
    ...
```

Never instantiate a session directly in a route or service. Never use the sync
SQLAlchemy session.

### pgvector queries

Always use parameterised queries for vector operations — never f-string SQL.

```python
# Correct — similarity search with metadata filter
result = await db.execute(
    text("""
        SELECT id, content, metadata, 1 - (embedding <=> :embedding) AS score
        FROM document_chunks
        WHERE workspace_id = :workspace_id
        ORDER BY embedding <=> :embedding
        LIMIT :limit
    """),
    {"embedding": embedding, "workspace_id": workspace_id, "limit": top_k},
)

# Wrong
query = f"SELECT ... ORDER BY embedding <=> '{embedding}' LIMIT {top_k}"
```

---

## Authentication

The `get_current_user` dependency in `backend/dependencies.py` decodes and validates
the JWT, then fetches the user from the database. Inject it on every protected route.

```python
from backend.dependencies import get_current_user
from backend.auth.models import User

@router.get("/protected")
async def protected(current_user: User = Depends(get_current_user)):
    ...
```

For admin-only routes use `Depends(require_admin)` from the same module.

Refresh tokens are stored in Redis as `refresh:{user_id}:{jti}`. Logout deletes
all keys matching `refresh:{user_id}:*` to invalidate all sessions.

Do not store anything sensitive (passwords, raw tokens) in the JWT payload. The
payload contains only `sub` (user id as string), `role`, and standard claims.

---

## Document ingestion pipeline

The ingestion flow must remain fully asynchronous. The HTTP upload endpoint does
**no parsing**. The sequence is:

1. `POST /documents/upload` — saves raw file to S3, creates DB row, enqueues task,
   returns `202` with `document_id`.
2. `workers/tasks.py:ingest_document(document_id)` — Celery task that runs the
   full pipeline: fetch → parse → chunk → embed → store → update status.
3. Frontend polls `GET /documents/{id}/status` until `"ready"` or `"failed"`.

When modifying the ingestion pipeline, ensure idempotency: the task should be safe
to retry. Each task stores its result under `ingest_result:{document_id}` in Redis
and short-circuits if that key exists and is `"success"`.

### Adding a new file type

1. Add a parser function in `ingestion/parsers.py` following the existing signature:
   `async def parse_<type>(file_bytes: bytes) -> list[PageContent]`.
2. Register it in the `PARSERS` dispatch dict at the top of `ingestion/pipeline.py`.
3. Add the file extension to the `ALLOWED_EXTENSIONS` set in `documents/service.py`.
4. Write a unit test in `tests/unit/test_parsers.py`.

---

## Agent loop

The ReAct loop lives in `agents/orchestrator.py`. The main entry point is:

```python
async def run_agent(
    query: str,
    session_id: str,
    user: User,
    event_queue: asyncio.Queue,  # SSE events go here
) -> AgentResult:
```

The loop calls OpenAI with `tool_choice="auto"`. On each iteration:

- If the response has `tool_calls` → execute each tool, push a `tool_call` SSE
  event, append the `tool` role message, continue.
- If the response is a plain message → push token events via streaming, push
  `done` event with citations, return.
- If `step_count >= settings.MAX_AGENT_STEPS` → raise `AgentStepLimitError`,
  which is caught in the streaming handler and sent as an `error` SSE event.

### Adding a new tool

1. Create `tools/<name>.py` with a class that extends `BaseTool` from `tools/base.py`.
2. Implement `async def run(self, **kwargs) -> ToolResult`.
3. Register the instance in `tools/registry.py`'s `TOOL_REGISTRY` dict.
4. The orchestrator reads the registry at startup — no other changes needed.
5. Write a unit test in `tests/unit/test_tools.py`.

```python
# tools/example_tool.py
from tools.base import BaseTool, ToolResult

class ExampleTool(BaseTool):
    name = "example"
    description = "Does an example thing. Use when the user needs X."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The input query."},
        },
        "required": ["query"],
    }

    async def run(self, query: str) -> ToolResult:
        result = await do_something(query)
        return ToolResult(content=result, metadata={"source": "example"})
```

---

## RAG pipeline

`rag/pipeline.py` exposes the main function `retrieve_and_assemble(query, workspace_id, top_k)`.

Internally it:

1. Rewrites the query via `rag/rewriter.py` (LLM call, cached per query hash in Redis).
2. Runs `vectorstore.similarity_search` and `vectorstore.keyword_search` in parallel.
3. Merges results with Reciprocal Rank Fusion (`k=60`).
4. Assembles a context string with citation IDs injected via `rag/citations.py`.
5. Returns `(context_str, chunks)` — the orchestrator appends both to the LLM prompt.

### Tuning retrieval

- Adjust `RETRIEVAL_TOP_K` in `.env` — increasing it improves recall but bloats
  the context window and raises cost.
- The RRF `k` constant is defined in `rag/pipeline.py:RRF_K = 60`. Lower values
  favour top-ranked results more aggressively.
- Query rewriting can be disabled by setting `RAG_REWRITE_QUERIES=false` in `.env`
  for latency-sensitive use cases.

---

## Streaming (SSE)

The streaming endpoint at `GET /chat/{session_id}/stream` returns
`Content-Type: text/event-stream`. It is implemented as a `StreamingResponse`
wrapping an async generator in `streaming/handler.py`.

Event types and their `data` payloads:

| Event        | Data fields                                           | When                             |
| ------------ | ----------------------------------------------------- | -------------------------------- |
| `token`      | `{"text": str}`                                       | Each streamed token from the LLM |
| `tool_call`  | `{"tool": str, "status": "running"\|"done"\|"error"}` | Agent tool execution             |
| `agent_step` | `{"step": int, "thought": str}`                       | Each ReAct iteration             |
| `citations`  | `{"items": list[Citation]}`                           | Immediately before `done`        |
| `done`       | `{"message_id": str}`                                 | Stream complete                  |
| `error`      | `{"code": str, "message": str}`                       | Any unrecoverable error          |

On the frontend, `useSSE.ts` handles `EventSource` lifecycle. It dispatches each
event type to the appropriate Zustand store action. The `done` event triggers a
refetch of conversation history.

Never buffer tokens server-side. Yield each `chunk.choices[0].delta.content`
from the OpenAI streaming response immediately into the event queue.

---

## Memory architecture

Two tiers, managed by `memory/service.py`:

**Short-term (Redis)** — raw conversation turns for the current session.
Key: `session:{session_id}:history`. TTL: 24 hours. Used to populate the
`messages` array on each LLM call. Flushed to DB on session end.

**Long-term (PostgreSQL)** — extracted facts and preferences keyed to a user.
After each turn, `memory/service.py:extract_and_store_memories(user_id, turn)`
runs asynchronously as a background task (not in the critical path). It prompts
the LLM to extract facts, embeds each fact, and stores them in `agent_memory`.
At retrieval time, the top-5 memories most similar to the current query are
prepended to the system prompt.

The sliding window summariser in `memory/summariser.py` activates when a session
exceeds `MEMORY_SUMMARISE_THRESHOLD` messages (default: 20). It summarises the
oldest half and replaces them with a single `summary` role message in Redis.
The originals remain in the DB.

---

## Error handling

All custom exceptions are in `common/exceptions.py`. Use these — do not raise
generic `Exception` or `HTTPException` directly from service or repository code.

| Exception              | HTTP status           | Use when                                          |
| ---------------------- | --------------------- | ------------------------------------------------- |
| `NotFoundError`        | 404                   | Resource does not exist or user lacks access      |
| `ValidationError`      | 422                   | Business rule violation (not Pydantic validation) |
| `AuthenticationError`  | 401                   | Missing or invalid credentials                    |
| `AuthorizationError`   | 403                   | Authenticated but not permitted                   |
| `IngestionError`       | 500                   | Document parsing or embedding failure             |
| `AgentStepLimitError`  | 200 (SSE error event) | Agent hit MAX_AGENT_STEPS                         |
| `ExternalServiceError` | 502                   | OpenAI, Tavily, or S3 call failed after retries   |

The global exception handler in `main.py` maps these to JSON error responses
with `{"error": {"code": ..., "message": ...}}` shape.

For external API calls, wrap with `tenacity`:

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(openai.RateLimitError),
)
async def call_openai(...):
    ...
```

---

## Testing

```bash
# Unit tests only (no Docker needed)
uv run pytest tests/unit -v

# Integration tests (requires Docker Compose test stack)
docker compose -f docker-compose.test.yml up -d
uv run pytest tests/integration -v
docker compose -f docker-compose.test.yml down
```

### Conventions

- Unit tests mock all I/O: database, Redis, OpenAI, S3. Use `pytest-mock` and
  `unittest.mock.AsyncMock` for async coroutines.
- Integration tests use a real test database. Fixtures in `conftest.py` create
  a fresh schema per test session and roll back transactions per test.
- Every new service function must have at least one unit test.
- Every new API route must have at least one integration test using `httpx.AsyncClient`.
- Test files mirror the source layout: `tests/unit/test_rag_pipeline.py` tests
  `backend/rag/pipeline.py`.
- Minimum coverage threshold: 80% (enforced in CI via `pytest --cov --cov-fail-under=80`).

---

## Logging and observability

Use `structlog` for all logging. Never use `print()` or the stdlib `logging` module
directly in application code.

```python
import structlog
log = structlog.get_logger(__name__)

# Correct — structured key/value context
log.info("document.ingested", document_id=str(doc.id), chunk_count=len(chunks))

# Wrong
print(f"Ingested document {doc.id}")
```

Every request is logged with `user_id`, `session_id`, `path`, `method`,
`status_code`, and `latency_ms` by the middleware in `main.py`.

Prometheus metrics are exposed at `GET /metrics`. Key metrics:

- `rag_retrieval_latency_seconds` — histogram of retrieval pipeline duration
- `agent_steps_total` — counter of agent loop iterations, labelled by tool name
- `openai_tokens_used_total` — counter, labelled by model and usage type
- `document_ingestion_duration_seconds` — histogram of full ingestion pipeline
- `celery_task_failures_total` — counter of failed Celery tasks by task name

---

## Code style

- Line length: 100 characters.
- Imports: sorted by `ruff` — stdlib, then third-party, then local. No star imports.
- All public functions must have type annotations on all parameters and return types.
- All public functions must have a one-line docstring. Complex logic gets an
  extended docstring with Args/Returns sections.
- Async all the way — no `time.sleep()`, no sync DB calls, no blocking I/O in
  route handlers or service functions. Offload blocking work to a thread pool
  via `asyncio.to_thread()` if unavoidable (e.g. in parsers using sync libraries).
- Pydantic models for all request bodies and response schemas. Never return raw
  SQLAlchemy model instances from routes — always map to a schema first.
- Use `from __future__ import annotations` at the top of every Python file to
  defer annotation evaluation.

---

## Commit conventions

Follow Conventional Commits: `type(scope): description`.

Common types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`.
Common scopes: `auth`, `rag`, `agents`, `ingestion`, `streaming`, `workers`, `frontend`.

Examples:

```
feat(rag): add reciprocal rank fusion to hybrid retrieval
fix(agents): prevent infinite loop when tool returns empty result
perf(embeddings): batch embed requests to reduce OpenAI round trips
test(ingestion): add integration test for PDF parser with scanned pages
```

Breaking changes must include `BREAKING CHANGE:` in the commit body and bump
the major version in `pyproject.toml`.

---

## Common tasks

### Add a new API endpoint

1. Add the route to the relevant module's `router.py`.
2. Add business logic to `service.py` — keep routes thin.
3. Add DB access to `repository.py` — keep service functions DB-agnostic.
4. Define request/response Pydantic models in `schemas.py`.
5. Register the router in `main.py` if it's a new module.
6. Write an integration test in `tests/integration/`.

### Add a new database table

1. Create or update the SQLAlchemy model in the relevant `models.py`.
2. Run `alembic revision --autogenerate -m "description"`.
3. Review the generated migration file carefully.
4. Run `alembic upgrade head` to apply.

### Change the chunking strategy

Edit `ingestion/chunker.py`. Re-ingest affected documents by setting their status
back to `"pending"` and re-enqueuing the Celery task. Do not modify existing
chunks in-place — delete them and re-insert.

### Change the embedding model

1. Update `OPENAI_EMBEDDING_MODEL` and `EMBEDDING_DIMENSIONS` in `.env`.
2. Update the `vector(N)` dimension in the `document_chunks` migration.
3. Flush the embedding cache: `redis-cli FLUSHDB` (dev only) or delete keys
   matching `emb:*`.
4. Re-ingest all documents — existing vectors are incompatible with a new model.

### Rotate JWT secret

1. Update `JWT_SECRET` in `.env` and redeploy.
2. All existing tokens are immediately invalidated — users must log in again.
3. Flush Redis refresh tokens: delete all keys matching `refresh:*`.

---

## What not to do

- Do not use synchronous SQLAlchemy sessions anywhere in the async FastAPI app.
- Do not call `openai.ChatCompletion.create` (sync) — always use the async client.
- Do not store embeddings as JSON arrays in a text column — use the `vector` type.
- Do not run Alembic migrations inside the application startup lifespan — run them
  as a separate step in the deployment pipeline.
- Do not put secrets in `config.py` defaults — defaults must be safe for
  public repositories. Secrets have no default and will raise `ValidationError`
  on startup if missing.
- Do not catch bare `Exception` and swallow it — at minimum log it and re-raise
  or convert to a typed application exception.
- Do not write multi-hundred-line service functions — if a function exceeds ~60
  lines it probably needs to be split.
- Do not bypass the repository layer and write raw SQL in `service.py`.
- Do not commit `.env` — it is gitignored. Use `.env.example` for documentation.
