from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_cookie_names, get_current_user
from app.core.config import get_settings
from app.core.security import create_access_token, decode_token
from app.db.database import get_db_session
from app.models.models import User
from app.schemas.auth import AuthResponse, AuthUser, LoginRequest, RegisterRequest
from app.schemas.common import MessageResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
auth_service = AuthService()


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    settings = get_settings()
    access_cookie_name, refresh_cookie_name = get_cookie_names()

    # Tokens in HTTP-only cookies reduce XSS token theft risk versus localStorage.
    response.set_cookie(
        key=access_cookie_name,
        value=access_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )
    response.set_cookie(
        key=refresh_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.refresh_token_expire_minutes * 60,
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    settings = get_settings()
    access_cookie_name, refresh_cookie_name = get_cookie_names()
    response.delete_cookie(access_cookie_name, path="/", secure=settings.cookie_secure, samesite=settings.cookie_samesite)
    response.delete_cookie(refresh_cookie_name, path="/", secure=settings.cookie_secure, samesite=settings.cookie_samesite)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_db_session),
) -> AuthResponse:
    user = await auth_service.register(session=session, payload=payload)
    return AuthResponse(user=AuthUser.model_validate(user))


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> AuthResponse:
    user, access_token, refresh_token = await auth_service.login(session=session, payload=payload)
    _set_auth_cookies(response, access_token, refresh_token)
    return AuthResponse(user=AuthUser.model_validate(user))


@router.post("/refresh", response_model=MessageResponse)
async def refresh_session(request: Request, response: Response) -> MessageResponse:
    settings = get_settings()
    refresh_cookie_name = settings.refresh_cookie_name
    refresh_token: str | None = request.cookies.get(refresh_cookie_name)

    if refresh_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token.")

    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token type.")

    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")

    access_token = create_access_token(subject=subject)
    _set_auth_cookies(response=response, access_token=access_token, refresh_token=refresh_token)
    return MessageResponse(message="Session refreshed.")


@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response) -> MessageResponse:
    _clear_auth_cookies(response)
    return MessageResponse(message="Logged out.")


@router.get("/me", response_model=AuthResponse)
async def current_user(user: User = Depends(get_current_user)) -> AuthResponse:
    return AuthResponse(user=AuthUser.model_validate(user))
