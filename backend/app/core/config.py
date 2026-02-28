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

    jwt_secret_key: str = Field(alias="JWT_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_minutes: int = 60 * 24 * 7

    auth_cookie_name: str = "grm_access_token"
    refresh_cookie_name: str = "grm_refresh_token"
    cookie_secure: bool = True
    cookie_samesite: str = "lax"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    # Caching avoids re-parsing env vars on every request and keeps dependency injection cheap.
    return Settings()
