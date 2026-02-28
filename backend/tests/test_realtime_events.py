from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from app.models.models import Alert
from app.services.realtime_events import publish_alert_event, serialize_alert_event


class FakeRedis:
    def __init__(self) -> None:
        self.channel: str | None = None
        self.message: str | None = None

    async def publish(self, channel: str, message: str) -> int:
        self.channel = channel
        self.message = message
        return 1


@pytest.mark.asyncio
async def test_publish_alert_event_uses_configured_channel() -> None:
    redis = FakeRedis()
    alert = Alert(
        id=101,
        severity_level="high",
        region="Black Sea",
        description="Critical shipping corridor disruption",
        source="internal-intel",
        timestamp=datetime.now(UTC),
    )

    await publish_alert_event(redis=redis, alert=alert)

    assert redis.channel == "georisk:alerts:events"
    assert redis.message is not None
    payload = json.loads(redis.message)
    assert payload["event"] == "alert.created"
    assert payload["payload"]["id"] == 101
    assert payload["payload"]["region"] == "Black Sea"


def test_serialize_alert_event_structure() -> None:
    alert = Alert(
        id=202,
        severity_level="critical",
        region="Middle East",
        description="Strategic chokepoint closure",
        source="partner-feed",
        timestamp=datetime.now(UTC),
    )

    payload = serialize_alert_event(alert)

    assert payload["event"] == "alert.created"
    assert payload["payload"]["id"] == 202
    assert payload["payload"]["severity_level"] == "critical"
    assert payload["payload"]["source"] == "partner-feed"
