from __future__ import annotations

from typing import cast

from fastapi import Request
from redis.asyncio import Redis

from app.core.config import get_settings


def build_redis_client() -> Redis:
    settings = get_settings()
    redis_client = Redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=None,
        retry_on_timeout=True,
    )
    return cast(Redis, redis_client)


def get_redis_client(request: Request) -> Redis:
    return cast(Redis, request.app.state.redis)
