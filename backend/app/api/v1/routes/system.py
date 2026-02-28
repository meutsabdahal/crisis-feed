from __future__ import annotations

from inspect import isawaitable
from typing import Awaitable
from typing import Any
from typing import TypeVar
from typing import cast

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.db.redis import get_redis_client

from app.core.config import get_settings

router = APIRouter(prefix="/system", tags=["system"])
T = TypeVar("T")


async def _resolve(value: Awaitable[T] | T) -> T:
    if isawaitable(value):
        return await cast(Awaitable[T], value)
    return value


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "georisk-monitor-api"}


@router.get("/health/db")
async def database_health_check(
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, Any]:
    await session.execute(text("SELECT 1"))
    return {"status": "ok", "database": "reachable"}


@router.get("/health/redis")
async def redis_health_check(
    redis: Redis = Depends(get_redis_client),
) -> dict[str, Any]:
    await redis.ping()
    return {"status": "ok", "redis": "reachable"}


@router.get("/metrics")
async def system_metrics(
    session: AsyncSession = Depends(get_db_session),
    redis: Redis = Depends(get_redis_client),
) -> dict[str, Any]:
    settings = get_settings()

    await session.execute(text("SELECT 1"))
    await redis.ping()

    ingestion_depth = await _resolve(redis.llen(settings.alert_ingestion_queue_key))
    dead_letter_depth = await _resolve(
        redis.llen(settings.alert_ingestion_dead_letter_queue_key)
    )

    return {
        "status": "ok",
        "database": "reachable",
        "redis": "reachable",
        "queues": {
            "ingestion": {
                "name": settings.alert_ingestion_queue_key,
                "depth": int(ingestion_depth),
            },
            "dead_letter": {
                "name": settings.alert_ingestion_dead_letter_queue_key,
                "depth": int(dead_letter_depth),
            },
        },
    }
