"""Application settings loaded from environment variables."""

from functools import lru_cache

from fastapi import Request
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed runtime configuration shared by FastAPI and Alembic."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "development"
    app_name: str = "사이42 API"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite+aiosqlite:///./data/sai42.db"
    cors_allowed_origins: str = "http://localhost:5173"
    sqlite_busy_timeout_ms: int = Field(default=5000, ge=0, le=60000)
    auth_rate_limit_max_attempts: int = Field(default=10, ge=1, le=100)
    auth_rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)
    openai_api_key: SecretStr | None = None
    weather_api_base_url: str = "https://api.open-meteo.com/v1/forecast"
    weather_api_timeout_seconds: float = Field(default=5.0, gt=0, le=30)

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        """Keep the application on the async SQLite contract."""
        if not value.startswith("sqlite+aiosqlite:///"):
            raise ValueError("DATABASE_URL은 sqlite+aiosqlite 비동기 URL이어야 합니다.")
        return value

    @field_validator("cors_allowed_origins")
    @classmethod
    def validate_cors_allowed_origins(cls, value: str) -> str:
        """Validate a comma-separated list of explicit browser origins."""
        origins = [origin.strip().rstrip("/") for origin in value.split(",") if origin.strip()]
        if not origins:
            raise ValueError("CORS_ALLOWED_ORIGINS에는 하나 이상의 origin이 필요합니다.")
        if any(not origin.startswith(("http://", "https://")) for origin in origins):
            raise ValueError("CORS origin은 http:// 또는 https://로 시작해야 합니다.")
        return ",".join(origins)

    @property
    def cors_origins(self) -> list[str]:
        """Return normalized origins for Starlette CORSMiddleware."""
        return self.cors_allowed_origins.split(",")


@lru_cache
def get_settings() -> Settings:
    """Return one immutable-by-convention settings instance per process."""
    return Settings()


def get_request_settings(request: Request) -> Settings:
    """Resolve the settings attached to the current application instance."""
    return request.app.state.settings
