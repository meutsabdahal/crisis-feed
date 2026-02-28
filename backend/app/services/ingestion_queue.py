from __future__ import annotations

import json
from inspect import isawaitable
from typing import Awaitable, TypeVar, cast
from uuid import uuid4

from redis.asyncio import Redis

from app.core.config import get_settings
from app.schemas.ingestion import AlertIngestionRequest, IngestionEnqueueResponse

T = TypeVar("T")


async def _resolve(value: Awaitable[T] | T) -> T:
    if isawaitable(value):
        return await cast(Awaitable[T], value)
    return value


async def enqueue_alert_ingestion(
    redis: Redis,
    payload: AlertIngestionRequest,
) -> IngestionEnqueueResponse:
    settings = get_settings()
    job_id = str(uuid4())

    message = {
        "job_id": job_id,
        "severity_level": payload.severity_level,
        "region": payload.region,
        "description": payload.description,
        "source": payload.source,
    }

    await _resolve(redis.rpush(settings.alert_ingestion_queue_key, json.dumps(message)))

    return IngestionEnqueueResponse(
        job_id=job_id,
        queue=settings.alert_ingestion_queue_key,
        status="queued",
    )
