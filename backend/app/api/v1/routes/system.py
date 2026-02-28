from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "georisk-monitor-api"}


@router.get("/health/db")
async def database_health_check(session: AsyncSession = Depends(get_db_session)) -> dict[str, Any]:
    await session.execute(text("SELECT 1"))
    return {"status": "ok", "database": "reachable"}
