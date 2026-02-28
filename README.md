# Crisis Feed

Crisis Feed is a lightweight, real-time news aggregator that surfaces high-priority conflict alerts from major international news sources. It polls public RSS feeds, filters articles by geopolitical relevance, and presents them through a server-rendered dashboard that auto-refreshes every 15 seconds.

---

## Table of Contents

- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Data Model](#data-model)
- [Ingestion Pipeline](#ingestion-pipeline)
- [API Reference](#api-reference)
- [Frontend](#frontend)
- [Prerequisites](#prerequisites)
- [Local Development](#local-development)
- [Docker Compose](#docker-compose)
- [Available Make Targets](#available-make-targets)
- [Continuous Integration](#continuous-integration)
- [Environment Variables](#environment-variables)
- [Deployment](#deployment)
- [License](#license)

---

## Architecture

```
RSS Feeds (7 sources)
        |
        v
  [Ingestion Loop]  -- polls every 3 min, filters by keyword relevance
        |
        v
  [SQLite (WAL mode)]  -- single-file database, no external dependencies
        |
        v
  [FastAPI backend]  -- serves JSON API on port 8000
        |
        v
  [Next.js frontend]  -- server-renders the feed, auto-refreshes via Script tag
```

The backend runs a background `asyncio` task that fetches all RSS feeds concurrently, filters entries for conflict relevance, and stores new alerts in SQLite. The frontend is a server-rendered Next.js page that fetches from the backend API at request time and injects a `setTimeout` reload for auto-refresh.

---

## Tech Stack

| Layer      | Technology                                     |
|------------|------------------------------------------------|
| Backend    | Python 3.12, FastAPI, SQLAlchemy (async), aiosqlite |
| Ingestion  | httpx, feedparser, asyncio.gather              |
| Database   | SQLite with WAL journal mode                   |
| Frontend   | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| Icons      | lucide-react                                   |
| Linting    | Ruff (Python), ESLint (TypeScript)             |
| Type Check | mypy (Python), tsc (TypeScript)                |
| CI         | GitHub Actions                                 |

---

## Project Structure

```
georisk_monitor/
  backend/
    app/
      __init__.py
      database.py       # SQLAlchemy async engine, session factory, init_db
      ingestion.py       # RSS polling, keyword filtering, source resolution
      main.py            # FastAPI app, lifespan, /api/alerts endpoint
      models.py          # NewsAlert ORM model
    Dockerfile
    .dockerignore
    pyproject.toml       # Python dependencies and tool config
  frontend/
    app/
      error.tsx          # Error boundary page
      global-error.tsx   # Root error boundary
      globals.css        # Tailwind base styles, dark theme
      layout.tsx         # Root layout with metadata
      page.tsx           # Main feed page (server-rendered)
    src/
      lib/
        types.ts         # NewsAlert TypeScript type
      types/
        env.d.ts         # Environment variable type declarations
    Dockerfile
    .dockerignore
    .env.example         # Example environment config
    next.config.mjs
    package.json
    tailwind.config.ts
    tsconfig.json
  .github/
    workflows/
      ci.yml             # Backend and frontend CI checks
  docker-compose.yml
  Makefile
  .gitignore
  README.md
```

---

## Data Model

Single table: `news_alerts`

| Column         | Type           | Constraints                  | Description                              |
|----------------|----------------|------------------------------|------------------------------------------|
| `id`           | Integer        | Primary key, auto-increment  | Unique identifier                        |
| `headline`     | String(500)    | Not null                     | Article title                            |
| `description`  | String(4000)   | Nullable                     | Cleaned excerpt from RSS summary/content |
| `source`       | String(255)    | Not null                     | Publisher name (e.g. "Reuters", "BBC")   |
| `url`          | String(1024)   | Unique, indexed, not null    | Link to the original article             |
| `published_at` | DateTime       | Indexed, not null            | Publication timestamp (UTC, naive)       |
| `is_breaking`  | Boolean        | Not null, default false      | Whether the alert matches breaking hints |

The database uses SQLite with `PRAGMA journal_mode=WAL` and `PRAGMA synchronous=NORMAL` for safe concurrent reads during writes.

---

## Ingestion Pipeline

The ingestion loop runs as a background `asyncio` task inside the FastAPI lifespan. Every 180 seconds it:

1. Fetches all 7 RSS feeds concurrently using `asyncio.gather`.
2. Parses each feed with `feedparser`.
3. Filters entries using a dual-keyword system: an article must contain at least one **actor keyword** (e.g. "iran", "israel", "u.s.") AND at least one **conflict keyword** (e.g. "strike", "missile", "attack").
4. Batch-checks which URLs already exist in the database using a single `WHERE url IN (...)` query per feed.
5. Inserts new alerts and backfills missing descriptions on existing records.
6. Resolves human-readable source names from a domain-to-publisher mapping (e.g. `bbc.co.uk` becomes "BBC").
7. Marks alerts as "breaking" if the headline contains hints like "breaking", "urgent", or "escalation".

### RSS Sources

| Source        | Feed URL                                             |
|---------------|------------------------------------------------------|
| Reuters       | `https://feeds.reuters.com/reuters/worldNews`        |
| CNN           | `http://rss.cnn.com/rss/edition_world.rss`           |
| Al Jazeera    | `https://www.aljazeera.com/xml/rss/all.xml`          |
| BBC           | `http://feeds.bbci.co.uk/news/world/rss.xml`         |
| NPR           | `https://feeds.npr.org/1004/rss.xml`                 |
| The Guardian  | `https://www.theguardian.com/world/rss`              |
| DW            | `https://rss.dw.com/rdf/rss-en-world`                |

---

## API Reference

### GET /api/alerts

Returns the most recent 100 alerts ordered by `published_at` descending.

**Response**: `200 OK`

```json
[
  {
    "id": 1,
    "headline": "Iran launches retaliatory strikes",
    "description": "Iran fired missiles at targets in...",
    "source": "Reuters",
    "url": "https://www.reuters.com/world/...",
    "published_at": "2026-02-28T12:00:00",
    "is_breaking": true
  }
]
```

On database errors the endpoint returns an empty array `[]` rather than a 500 status.

---

## Frontend

The feed page is a server-rendered async React component. On each request it:

1. Fetches alerts from `GET /api/alerts` at the server level (no client-side JavaScript needed for the initial render).
2. Displays alerts as cards with source label, timestamp, headline, description excerpt (truncated to 280 characters), and a "BREAKING" badge for flagged items.
3. Shows summary stats in the header: total alert count, number of distinct sources, and breaking alert count.
4. Supports pagination through a `?limit=` query parameter. The default page size is 20 alerts, with a "Load more" button that increments the limit by 20 up to the API maximum of 100.
5. Auto-refreshes the page every 15 seconds using a `<Script>` tag that calls `setTimeout` with `window.location.reload()`.

---

## Prerequisites

- **Python 3.12+** with [uv](https://docs.astral.sh/uv/) installed
- **Node.js 18+** with npm

Verify with:

```bash
make doctor
```

---

## Local Development

### 1. Install dependencies

```bash
cd backend && uv sync
cd ../frontend && npm install
```

### 2. Start the backend (terminal 1)

```bash
make backend
```

The API will be available at `http://127.0.0.1:8000`. The ingestion loop starts automatically and begins polling RSS feeds.

### 3. Start the frontend (terminal 2)

```bash
make frontend
```

The dashboard will be available at `http://localhost:3000`.

### Custom ports

```bash
make backend BACKEND_PORT=9000
```

---

## Docker Compose

Build and run both services:

```bash
docker compose up --build
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

The SQLite database file is mounted as a volume at `./backend/crisis_feed.db` so data persists across container restarts.

---

## Available Make Targets

| Target            | Description                                          |
|-------------------|------------------------------------------------------|
| `make doctor`     | Verify that `uv` and `npm` are installed             |
| `make backend`    | Start the FastAPI backend with hot reload             |
| `make frontend`   | Start the Next.js development server                 |
| `make dev`        | Print instructions for running both services         |
| `make lint-backend`   | Run Ruff linter on backend code                  |
| `make type-backend`   | Run mypy type checker on backend code            |
| `make lint-frontend`  | Run ESLint on frontend code                      |
| `make type-frontend`  | Run TypeScript compiler in check-only mode       |
| `make build-frontend` | Create a production build of the frontend        |
| `make clean`          | Remove build artifacts, caches, and database files |

---

## Continuous Integration

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push and pull request to `main`. It performs the following checks:

**Backend job:**
- Ruff lint
- mypy type check
- Byte-compilation of all modules
- Import smoke test for the ingestion module

**Frontend job:**
- ESLint
- TypeScript type check (`tsc --noEmit`)
- Production build (`next build`)

---

## Environment Variables

### Frontend

| Variable                    | Default                    | Description                       |
|-----------------------------|----------------------------|-----------------------------------|
| `NEXT_PUBLIC_API_BASE_URL`  | `http://localhost:8000`    | Backend API origin for fetch calls |

Set this in `frontend/.env.local` for local development or pass it at build time for production.

### Backend

The backend has no required environment variables. The SQLite database path is hardcoded to `./crisis_feed.db` relative to the working directory.

---

## Deployment

The project is designed to run on free-tier hosting platforms. Recommended options:

| Platform | Backend | Frontend | Notes |
|----------|---------|----------|-------|
| Render   | Free Web Service (Python) | Free Static Site or Web Service | Supports persistent disk for SQLite. Auto-deploys from GitHub. |
| Railway  | Free trial ($5 credit/mo) | Same service | Supports volumes for SQLite persistence. Docker-based deploy. |
| Fly.io   | Free tier (3 shared VMs) | Same | Persistent volumes available. Requires the flyctl CLI. |
| Vercel + Render | Backend on Render | Frontend on Vercel | Vercel is zero-config for Next.js. Set `NEXT_PUBLIC_API_BASE_URL` to the Render URL. |

When deploying, set the `NEXT_PUBLIC_API_BASE_URL` environment variable on the frontend to point to the deployed backend URL.

---

## License

This project is provided as-is for educational and personal use.