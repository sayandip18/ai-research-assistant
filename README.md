# AI Research Assistant

## Tech Stack

**Backend**
- Python 3.12, FastAPI, SQLAlchemy (async), Alembic
- PostgreSQL + pgvector, Redis
- OpenAI API, Celery, MinIO (S3-compatible storage)
- bcrypt, python-jose (JWT), structlog, Prometheus

**Frontend**
- React 18, TypeScript, Vite
- Zustand (state management)

---

## Running the project

### Prerequisites
- Docker and Docker Compose
- Node 20+ and pnpm

### 1. Configure environment

```bash
cp backend/.env.example backend/.env
```

Open `backend/.env` and fill in at minimum:

```
JWT_SECRET=<random string, at least 32 characters>
OPENAI_API_KEY=<your key>
```

### 2. Start backend services

```bash
docker compose up -d
```

This starts the API, Celery worker, PostgreSQL, Redis, and MinIO.

### 3. Run database migrations

```bash
docker compose run --rm api alembic upgrade head
```

### 4. Start the frontend dev server

```bash
cd frontend
pnpm install
pnpm dev
```

The app is available at **http://localhost:5173**.  
The API is available at **http://localhost:8000** (docs at `/docs`).

### Rebuilding after dependency changes

```bash
docker compose up --build
```

### Running tests

```bash
# Unit tests (no Docker required)
uv run pytest tests/unit -v

# Integration tests
docker compose -f docker-compose.test.yml up -d
uv run pytest tests/integration -v
docker compose -f docker-compose.test.yml down
```
