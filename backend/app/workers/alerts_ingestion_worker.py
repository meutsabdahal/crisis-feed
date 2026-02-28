from __future__ import annotations

import asyncio
import json
import logging
from datetime import UTC, datetime
from typing import Any

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.db.database import build_engine, build_session_factory
from app.db.redis import build_redis_client
from app.models.models import Alert

LOGGER: logging.Logger = logging.getLogger(__name__)


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


async def run_worker() -> None:
    settings = get_settings()
    redis: Redis = build_redis_client()
    engine = build_engine()
    session_factory: async_sessionmaker[AsyncSession] = build_session_factory(engine)

    LOGGER.info("Starting alert ingestion worker")

    try:
        while True:
            item = await redis.blpop(settings.alert_ingestion_queue_key, timeout=5)
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
    finally:
        await redis.aclose()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_worker())
