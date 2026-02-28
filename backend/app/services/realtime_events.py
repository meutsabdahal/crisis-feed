from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from inspect import isawaitable
from typing import Any, Awaitable, TypeVar, cast

from redis.asyncio import Redis

from app.core.config import get_settings
from app.models.models import Alert
from app.schemas.alerts import AlertRead

T = TypeVar("T")


async def _resolve(value: Awaitable[T] | T) -> T:
    if isawaitable(value):
        return await cast(Awaitable[T], value)
    return value


def serialize_alert_event(alert: Alert) -> dict[str, Any]:
    alert_payload = AlertRead.model_validate(alert).model_dump(mode="json")
    return {
        "event": "alert.created",
        "payload": alert_payload,
    }


async def publish_alert_event(redis: Redis, alert: Alert) -> None:
    settings = get_settings()
    message = json.dumps(serialize_alert_event(alert))
    await _resolve(redis.publish(settings.alert_events_channel, message))


async def stream_alert_events(redis: Redis) -> AsyncIterator[str]:
    settings = get_settings()
    pubsub = redis.pubsub(ignore_subscribe_messages=True)
    await pubsub.subscribe(settings.alert_events_channel)

    try:
        while True:
            message = await pubsub.get_message(timeout=5.0)
            if isinstance(message, dict):
                data = message.get("data")
                if isinstance(data, bytes):
                    yield data.decode("utf-8")
                elif isinstance(data, str):
                    yield data
            await asyncio.sleep(0.1)
    finally:
        await pubsub.unsubscribe(settings.alert_events_channel)
        await pubsub.close()
