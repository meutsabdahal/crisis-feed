from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime
from inspect import isawaitable
from typing import Any, Awaitable, TypeVar, cast

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.db.database import build_engine, build_session_factory
from app.db.redis import build_redis_client
from app.models.models import Alert

LOGGER: logging.Logger = logging.getLogger(__name__)
T = TypeVar("T")


async def _resolve(value: Awaitable[T] | T) -> T:
    if isawaitable(value):
        return await cast(Awaitable[T], value)
    return value


async def process_job(session: AsyncSession, job_payload: dict[str, Any]) -> None:
    alert = Alert(
        severity_level=str(job_payload["severity_level"]),
        region=str(job_payload["region"]),
        description=str(job_payload["description"]),
        source=str(job_payload["source"]),
        timestamp=datetime.now(UTC),
    )
    session.add(alert)
    await session.commit()


async def handle_failed_job(redis: Redis, job_payload: dict[str, Any]) -> None:
    settings = get_settings()
    retry_count = int(job_payload.get("retry_count", 0)) + 1
    job_payload["retry_count"] = retry_count

    if retry_count <= settings.alert_ingestion_max_retries:
        await _resolve(redis.rpush(settings.alert_ingestion_queue_key, json.dumps(job_payload)))
        LOGGER.warning(
            "Requeued failed ingestion job %s (retry %s/%s)",
            job_payload.get("job_id"),
            retry_count,
            settings.alert_ingestion_max_retries,
        )
        return

    await _resolve(
        redis.rpush(
            settings.alert_ingestion_dead_letter_queue_key,
            json.dumps(job_payload),
        )
    )
    LOGGER.error("Moved ingestion job %s to DLQ", job_payload.get("job_id"))


async def run_worker() -> None:
    settings = get_settings()
    redis: Redis = build_redis_client()
    engine = build_engine()
    session_factory: async_sessionmaker[AsyncSession] = build_session_factory(engine)

    LOGGER.info("Starting alert ingestion worker")

    try:
        while True:
            item = await _resolve(redis.blpop([settings.alert_ingestion_queue_key], timeout=5))
            if item is None:
                continue

            _, raw_payload = item
            try:
                payload = json.loads(raw_payload)
                async with session_factory() as session:
                    await process_job(session, payload)
                LOGGER.info("Processed ingestion job %s", payload.get("job_id"))
            except Exception:
                LOGGER.exception("Failed to process ingestion job payload")
                if isinstance(raw_payload, str):
                    failed_payload = json.loads(raw_payload)
                else:
                    failed_payload = json.loads(str(raw_payload))
                await handle_failed_job(redis=redis, job_payload=failed_payload)
    finally:
        await redis.aclose()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_worker())
