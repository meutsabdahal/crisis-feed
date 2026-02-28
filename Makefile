SHELL := /bin/bash

DATABASE_URL ?= postgresql+asyncpg://postgres:postgres@localhost:5432/georisk_monitor
JWT_SECRET_KEY ?= dev-local-secret
COOKIE_SECURE ?= false

.PHONY: backend worker test-backend lint-backend type-backend seed-alerts migrate migrate-sql dev-backend doctor

doctor:
	@echo "Checking local prerequisites..."
	@command -v uv >/dev/null 2>&1 && echo "[ok] uv" || (echo "[missing] uv" && exit 1)
	@command -v docker >/dev/null 2>&1 && echo "[ok] docker" || echo "[warn] docker not found (full stack compose unavailable)"
	@command -v npm >/dev/null 2>&1 && echo "[ok] npm" || echo "[warn] npm not found (frontend local dev unavailable)"
	@echo "Done."

backend:
	DATABASE_URL="$(DATABASE_URL)" JWT_SECRET_KEY="$(JWT_SECRET_KEY)" COOKIE_SECURE="$(COOKIE_SECURE)" \
	uv run --project backend uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload

migrate:
	cd backend && DATABASE_URL="$(DATABASE_URL)" JWT_SECRET_KEY="$(JWT_SECRET_KEY)" \
	uv run alembic upgrade head

migrate-sql:
	cd backend && DATABASE_URL="$(DATABASE_URL)" JWT_SECRET_KEY="$(JWT_SECRET_KEY)" \
	uv run alembic upgrade head --sql > /tmp/georisk_alembic.sql

dev-backend: migrate backend

worker:
	DATABASE_URL="$(DATABASE_URL)" JWT_SECRET_KEY="$(JWT_SECRET_KEY)" COOKIE_SECURE="$(COOKIE_SECURE)" PYTHONPATH=backend \
	uv run --project backend python -m app.workers.alerts_ingestion_worker

test-backend:
	cd backend && DATABASE_URL="$(DATABASE_URL)" JWT_SECRET_KEY="$(JWT_SECRET_KEY)" COOKIE_SECURE="$(COOKIE_SECURE)" \
	uv run pytest

lint-backend:
	cd backend && uv run ruff check app tests

type-backend:
	cd backend && uv run mypy app

seed-alerts:
	DATABASE_URL="$(DATABASE_URL)" JWT_SECRET_KEY="$(JWT_SECRET_KEY)" COOKIE_SECURE="$(COOKIE_SECURE)" PYTHONPATH=backend \
	uv run --project backend python -m app.scripts.seed_alerts --count 25
