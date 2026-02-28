from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.db.redis import get_redis_client

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "georisk-monitor-api"}


@router.get("/health/db")
async def database_health_check(session: AsyncSession = Depends(get_db_session)) -> dict[str, Any]:
    await session.execute(text("SELECT 1"))
    return {"status": "ok", "database": "reachable"}


@router.get("/health/redis")
async def redis_health_check(redis: Redis = Depends(get_redis_client)) -> dict[str, Any]:
    await redis.ping()
    return {"status": "ok", "redis": "reachable"}
