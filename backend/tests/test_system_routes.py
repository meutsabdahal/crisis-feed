from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi.testclient import TestClient

from app.db.database import get_db_session
from app.db.redis import get_redis_client
from app.main import create_app


class FakeSession:
    async def execute(self, _: object) -> None:
        return None


class FakeRedis:
    async def ping(self) -> bool:
        return True


async def fake_db_session() -> AsyncIterator[FakeSession]:
    yield FakeSession()


def fake_redis_client() -> FakeRedis:
    return FakeRedis()


def _build_test_client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_db_session] = fake_db_session
    app.dependency_overrides[get_redis_client] = fake_redis_client
    return TestClient(app)


def test_health_endpoint() -> None:
    with _build_test_client() as client:
        response = client.get("/api/v1/system/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "georisk-monitor-api"}


def test_database_health_endpoint() -> None:
    with _build_test_client() as client:
        response = client.get("/api/v1/system/health/db")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "reachable"}


def test_redis_health_endpoint() -> None:
    with _build_test_client() as client:
        response = client.get("/api/v1/system/health/redis")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "redis": "reachable"}
