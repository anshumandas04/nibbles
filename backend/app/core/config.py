"""Application settings loaded from environment variables via pydantic-settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration sourced from ``.env`` or environment variables."""

    APP_NAME: str = "CloudSync Backup"
    API_KEY: str = "unhackable-demo-key-change-me"
    DATABASE_URL: str = "postgresql+asyncpg://cloudsync:cloudsync_secret@db:5432/cloudsync_db"
    UPLOAD_DIR: str = "storage"
    MAX_UPLOAD_SIZE_MB: int = 500
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "change-me-to-a-random-secret-key-in-production"
    ALLOWED_ORIGINS: str = "http://localhost"
    CHUNK_READ_SIZE: int = 1_048_576  # 1 MB
    RATE_LIMIT: str = "100/minute"
    BUILD_VERSION: str = "1.0.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def max_upload_size_bytes(self) -> int:
        """Return the maximum upload size in bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1_024 * 1_024

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse comma-separated origins into a list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — call anywhere to retrieve config."""
    return Settings()
