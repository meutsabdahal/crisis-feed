from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_admin_user, get_current_user
from app.db.database import get_db_session
from app.models.models import User
from app.schemas.alerts import AlertCreate, AlertRead
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])
alert_service = AlertService()


@router.get("", response_model=list[AlertRead])
async def list_alerts(
    limit: int = Query(default=100, ge=1, le=500),
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> list[AlertRead]:
    alerts = await alert_service.list_alerts(session=session, limit=limit)
    return [AlertRead.model_validate(alert) for alert in alerts]


@router.post("", response_model=AlertRead, status_code=status.HTTP_201_CREATED)
async def create_alert(
    payload: AlertCreate,
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> AlertRead:
    alert = await alert_service.create_alert(session=session, payload=payload)
    return AlertRead.model_validate(alert)
