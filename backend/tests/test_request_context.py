from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def test_request_context_headers_present() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/api/v1/system/health")

    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert "x-response-time-ms" in response.headers


def test_request_context_preserves_request_id() -> None:
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/api/v1/system/health", headers={"x-request-id": "trace-123"})

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "trace-123"
