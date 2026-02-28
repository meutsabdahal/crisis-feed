from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

# Ensure required settings exist before importing app modules that call create_app at import time.
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/georisk_monitor",
)
os.environ.setdefault("JWT_SECRET_KEY", "test-only-secret-key")
os.environ.setdefault("COOKIE_SECURE", "false")

from app.core.config import get_settings
from app.main import create_app


@pytest.fixture(scope="session", autouse=True)
def configure_test_environment() -> Generator[None, None, None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
