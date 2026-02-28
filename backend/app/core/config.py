from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "GeoRisk Monitor API"
    app_version: str = "0.1.0"
    environment: str = "development"

    frontend_origin: str = Field(default="http://localhost:3000", alias="FRONTEND_ORIGIN")
    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    alert_ingestion_queue_key: str = Field(
        default="georisk:ingestion:alerts",
        alias="ALERT_INGESTION_QUEUE_KEY",
    )

    jwt_secret_key: str = Field(alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=15, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_minutes: int = Field(default=60 * 24 * 7, alias="REFRESH_TOKEN_EXPIRE_MINUTES")

    auth_cookie_name: str = Field(default="grm_access_token", alias="AUTH_COOKIE_NAME")
    refresh_cookie_name: str = Field(default="grm_refresh_token", alias="REFRESH_COOKIE_NAME")
    cookie_secure: bool = Field(default=False, alias="COOKIE_SECURE")
    cookie_samesite: str = Field(default="lax", alias="COOKIE_SAMESITE")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    # Caching avoids re-parsing env vars on every request and keeps dependency injection cheap.
    return Settings()
