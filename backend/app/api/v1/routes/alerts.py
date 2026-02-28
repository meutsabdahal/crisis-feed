from __future__ import annotations

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_admin_user, get_current_user
from app.core.security import decode_token
from app.db.database import get_db_session
from app.db.redis import build_redis_client, get_redis_client
from app.models.models import User
from app.schemas.alerts import AlertCreate, AlertRead
from app.schemas.ingestion import AlertIngestionRequest, IngestionEnqueueResponse
from app.services.alert_service import AlertService
from app.services.ingestion_queue import enqueue_alert_ingestion
from app.services.realtime_events import publish_alert_event, stream_alert_events
from app.core.config import get_settings

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
    redis: Redis = Depends(get_redis_client),
) -> AlertRead:
    alert = await alert_service.create_alert(session=session, payload=payload)
    await publish_alert_event(redis=redis, alert=alert)
    return AlertRead.model_validate(alert)


@router.post("/ingest", response_model=IngestionEnqueueResponse, status_code=status.HTTP_202_ACCEPTED)
async def enqueue_alert_ingestion_job(
    payload: AlertIngestionRequest,
    _: User = Depends(get_admin_user),
    redis: Redis = Depends(get_redis_client),
) -> IngestionEnqueueResponse:
    return await enqueue_alert_ingestion(redis=redis, payload=payload)


@router.websocket("/stream")
async def stream_alerts(websocket: WebSocket) -> None:
    settings = get_settings()
    access_token = websocket.cookies.get(settings.auth_cookie_name)
    if access_token is None:
        await websocket.close(code=1008, reason="Authentication required.")
        return

    try:
        payload = decode_token(access_token)
    except ValueError:
        await websocket.close(code=1008, reason="Invalid access token.")
        return

    if payload.get("type") != "access":
        await websocket.close(code=1008, reason="Invalid token type.")
        return

    await websocket.accept()
    redis = build_redis_client()
    try:
        async for event in stream_alert_events(redis):
            await websocket.send_text(event)
    except WebSocketDisconnect:
        return
    finally:
        await redis.aclose()
