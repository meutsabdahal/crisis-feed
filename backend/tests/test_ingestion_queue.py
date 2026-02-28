from __future__ import annotations

import json

import pytest

from app.schemas.ingestion import AlertIngestionRequest
from app.services.ingestion_queue import enqueue_alert_ingestion


class FakeRedis:
    def __init__(self) -> None:
        self.queue_key: str | None = None
        self.payload: str | None = None

    async def rpush(self, queue_key: str, payload: str) -> int:
        self.queue_key = queue_key
        self.payload = payload
        return 1


@pytest.mark.asyncio
async def test_enqueue_alert_ingestion_pushes_serialized_job() -> None:
    redis = FakeRedis()
    payload = AlertIngestionRequest(
        severity_level="high",
        region="Black Sea",
        description="Shipping lane disruption observed.",
        source="satellite-feed",
    )

    result = await enqueue_alert_ingestion(redis=redis, payload=payload)

    assert result.status == "queued"
    assert result.queue == "georisk:ingestion:alerts"
    assert result.job_id

    assert redis.queue_key == "georisk:ingestion:alerts"
    assert redis.payload is not None

    queued_payload = json.loads(redis.payload)
    assert queued_payload["job_id"] == result.job_id
    assert queued_payload["severity_level"] == payload.severity_level
    assert queued_payload["region"] == payload.region
    assert queued_payload["description"] == payload.description
    assert queued_payload["source"] == payload.source
