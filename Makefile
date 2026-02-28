SHELL := /bin/bash

BACKEND_PORT ?= 8000
FRONTEND_PORT ?= 3000

.PHONY: doctor backend frontend dev lint-backend type-backend lint-frontend type-frontend build-frontend clean

doctor:
	@echo "Checking local prerequisites..."
	@command -v uv >/dev/null 2>&1 && echo "[ok] uv" || (echo "[missing] uv" && exit 1)
	@command -v npm >/dev/null 2>&1 && echo "[ok] npm" || echo "[warn] npm not found (frontend local dev unavailable)"
	@echo "Done."

backend:
	uv run --project backend uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port $(BACKEND_PORT) --reload

frontend:
	cd frontend && npm run dev

dev:
	@echo "Start backend and frontend in separate terminals: make backend | make frontend"

lint-backend:
	cd backend && uv run ruff check app

type-backend:
	cd backend && uv run mypy app

lint-frontend:
	cd frontend && npm run lint

type-frontend:
	cd frontend && npm run typecheck

build-frontend:
	cd frontend && npm run build

clean:
	rm -rf frontend/.next frontend/tsconfig.tsbuildinfo
	find backend -type d -name "__pycache__" -prune -exec rm -rf {} +
	rm -rf backend/.ruff_cache backend/.mypy_cache backend/.pytest_cache
	rm -f crisis_feed.db crisis_feed.db-wal crisis_feed.db-shm
	rm -f backend/crisis_feed.db backend/crisis_feed.db-wal backend/crisis_feed.db-shm
