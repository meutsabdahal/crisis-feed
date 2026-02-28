from app.api.v1.routes.alerts import router as alerts_router
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.system import router as system_router

__all__ = ["alerts_router", "auth_router", "system_router"]
