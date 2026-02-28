from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.models.models import User
from app.schemas.auth import LoginRequest, RegisterRequest


class AuthService:
    async def register(self, session: AsyncSession, payload: RegisterRequest) -> User:
        existing_user = await session.scalar(
            select(User).where(User.email == payload.email)
        )
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email already exists.",
            )

        user = User(
            email=payload.email,
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            role="analyst",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    async def login(
        self, session: AsyncSession, payload: LoginRequest
    ) -> tuple[User, str, str]:
        user = await session.scalar(select(User).where(User.email == payload.email))
        if user is None or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive.",
            )

        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))
        return user, access_token, refresh_token
