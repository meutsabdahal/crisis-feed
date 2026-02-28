SHELL := /bin/bash

DATABASE_URL ?= postgresql+asyncpg://postgres:postgres@localhost:5432/georisk_monitor
JWT_SECRET_KEY ?= dev-local-secret
COOKIE_SECURE ?= false

.PHONY: backend worker test-backend lint-backend type-backend seed-alerts

backend:
	DATABASE_URL="$(DATABASE_URL)" JWT_SECRET_KEY="$(JWT_SECRET_KEY)" COOKIE_SECURE="$(COOKIE_SECURE)" \
	uv run --project backend uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload

worker:
	DATABASE_URL="$(DATABASE_URL)" JWT_SECRET_KEY="$(JWT_SECRET_KEY)" COOKIE_SECURE="$(COOKIE_SECURE)" PYTHONPATH=backend \
	uv run --project backend python -m app.workers.alerts_ingestion_worker

test-backend:
	DATABASE_URL="$(DATABASE_URL)" JWT_SECRET_KEY="$(JWT_SECRET_KEY)" COOKIE_SECURE="$(COOKIE_SECURE)" \
	uv run --project backend pytest

lint-backend:
	uv run --project backend ruff check backend/app backend/tests

type-backend:
	uv run --project backend mypy backend/app

seed-alerts:
	DATABASE_URL="$(DATABASE_URL)" JWT_SECRET_KEY="$(JWT_SECRET_KEY)" COOKIE_SECURE="$(COOKIE_SECURE)" PYTHONPATH=backend \
	uv run --project backend python -m app.scripts.seed_alerts --count 25
