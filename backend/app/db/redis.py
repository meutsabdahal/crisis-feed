from __future__ import annotations

from fastapi import Request
from redis.asyncio import Redis

from app.core.config import get_settings


def build_redis_client() -> Redis:
    settings = get_settings()
    return Redis.from_url(
        settings.redis_url,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True,
    )


def get_redis_client(request: Request) -> Redis:
    return request.app.state.redis
