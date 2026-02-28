# GeoRisk Monitor

GeoRisk Monitor is a production-oriented B2B SaaS baseline for real-time geopolitical risk monitoring.

## Architecture

- Backend: FastAPI + SQLAlchemy Async + PostgreSQL + Redis
- Frontend: Next.js App Router + TypeScript + Tailwind
- Auth: JWT in HTTP-only cookies
- Ingestion: Redis queue + worker + retry + dead-letter queue
- Real-time delivery: Redis pub/sub + WebSocket stream

## Project Structure

```text
georisk_monitor/
├── .github/workflows/ci.yml
├── backend/
│   ├── .env.example
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   └── models/
│   │   ├── scripts/
│   │   ├── services/
│   │   ├── workers/
│   │   └── main.py
│   └── tests/
├── frontend/
│   ├── .env.example
│   ├── Dockerfile
│   ├── package.json
│   ├── app/
│   └── src/
│       ├── components/
│       │   └── ui/
│       └── lib/
├── docker-compose.yml
├── Makefile
└── README.md
```

## Quick Start (From Repo Root)

### 1) Validate local tooling

```bash
make doctor
```

### 2) Prepare env files

```bash
make env-all
```

### 3) Start backend only (local)

```bash
make dev-backend
```

This runs migrations then starts API on `http://127.0.0.1:8000`.

### 4) Start ingestion worker (separate terminal)

```bash
make worker
```

### 5) Seed sample alerts (optional)

```bash
make seed-alerts
```

## Full Stack (Docker)

If Docker is installed:

```bash
docker compose up --build
```

Services:
- API: `http://localhost:8000`
- Frontend: `http://localhost:3000`
- Postgres: `localhost:5432`
- Redis: `localhost:6379`

## Core Make Targets

- `make backend` – run FastAPI with reload
- `make dev-backend` – migrate + run backend
- `make worker` – run alert ingestion worker
- `make migrate` – apply Alembic migrations
- `make migrate-sql` – render migration SQL to `/tmp/georisk_alembic.sql`
- `make seed-alerts` – insert synthetic alerts
- `make test-backend` – run backend tests
- `make lint-backend` – run Ruff
- `make type-backend` – run mypy

## API Health & Metrics

- `GET /api/v1/system/health`
- `GET /api/v1/system/health/db`
- `GET /api/v1/system/health/redis`
- `GET /api/v1/system/metrics`

## Real-Time Stream

- WebSocket endpoint: `ws://localhost:8000/api/v1/alerts/stream`
- Requires valid access-token cookie (`grm_access_token`)
- Event shape:

```json
{
	"event": "alert.created",
	"payload": {
		"id": 123,
		"severity_level": "critical",
		"region": "Middle East",
		"description": "...",
		"timestamp": "2026-02-28T12:00:00Z",
		"source": "internal-intel"
	}
}
```

## Common Troubleshooting

### `uv run uvicorn app.main:app --reload` fails at repo root

Run from root using:

```bash
make backend
```

or explicitly:

```bash
uv run --project backend uvicorn app.main:app --app-dir backend --reload
```

### Frontend local dev unavailable

Install Node/npm on your machine, then run:

```bash
cd frontend
npm install
npm run dev
```