from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes.alerts import router as alerts_router
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.system import router as system_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(system_router)
api_router.include_router(auth_router)
api_router.include_router(alerts_router)
