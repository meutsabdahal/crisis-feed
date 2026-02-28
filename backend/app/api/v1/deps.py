from __future__ import annotations

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import decode_token
from app.db.database import get_db_session
from app.models.models import User


async def get_current_user(
    session: AsyncSession = Depends(get_db_session),
    access_token: str | None = Cookie(default=None, alias="grm_access_token"),
) -> User:
    if access_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")

    payload = decode_token(access_token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type.")

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.isdigit():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject.")

    user = await session.scalar(select(User).where(User.id == int(subject)))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is unavailable.")

    return user


def get_cookie_names() -> tuple[str, str]:
    settings = get_settings()
    return settings.auth_cookie_name, settings.refresh_cookie_name
