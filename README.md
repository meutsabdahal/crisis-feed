# Crisis Feed

Crisis Feed is a lightweight, real-time news aggregator focused on high-priority conflict alerts.

## Stack

- Backend: FastAPI + SQLAlchemy Async + SQLite
- Ingestion: `httpx` + `feedparser` polling RSS every 3 minutes
- Frontend: Next.js App Router + TypeScript + Tailwind CSS

## Data Model

Single table: `news_alerts`

- `id`
- `headline`
- `source`
- `url`
- `published_at`
- `is_breaking`

## API

- `GET /api/alerts` → latest 100 alerts ordered by newest first

## Local Run

1. Install dependencies:

```bash
cd backend && uv sync
cd ../frontend && npm install
```

2. Start backend:

```bash
make backend
```

3. Start frontend (separate terminal):

```bash
make frontend
```

Frontend polls the backend every 15 seconds and highlights breaking alerts.

## Helpful Commands

- `make doctor`
- `make lint-backend`
- `make type-backend`
- `make lint-frontend`
- `make type-frontend`
- `make build-frontend`