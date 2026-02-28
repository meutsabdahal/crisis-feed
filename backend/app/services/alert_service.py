from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Alert
from app.schemas.alerts import AlertCreate


class AlertService:
    async def list_alerts(self, session: AsyncSession, limit: int = 100) -> list[Alert]:
        statement = select(Alert).order_by(desc(Alert.timestamp)).limit(limit)
        result = await session.scalars(statement)
        return list(result)

    async def create_alert(self, session: AsyncSession, payload: AlertCreate) -> Alert:
        alert = Alert(
            severity_level=payload.severity_level,
            region=payload.region,
            description=payload.description,
            source=payload.source,
        )
        session.add(alert)
        await session.commit()
        await session.refresh(alert)
        return alert
