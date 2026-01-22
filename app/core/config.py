"""
Application configuration.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from functools import lru_cache
import warnings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "EdTech Word Chain API"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/wordchain.db"
    db_pool_size: int = 20
    db_max_overflow: int = 30
    db_pool_timeout: int = 30

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Authentication
    secret_key: str = "nYGsAi-MC7y_ACqPuHF7VGNn1bqx2IqOXG2I3rnFiuMULmxyP3ent5xdGZSaDbWZ1bU6nOLpk-l2RkwEJDrG5g"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Password Reset
    password_reset_token_expire_minutes: int = 60
    email_verification_token_expire_hours: int = 24

    # Email (Mailjet)
    mailjet_api_key: Optional[str] = None
    mailjet_api_secret: Optional[str] = None
    mailjet_sender_email: str = "noreply@example.com"
    mailjet_sender_name: str = "EdTech Word Chain"

    # Frontend & CORS
    frontend_url: str = "http://localhost:3000"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Game Settings
    min_word_length: int = 3
    max_word_length: int = 6
    default_game_mode: str = "STANDARD"

    # XP Settings
    xp_per_valid_move: int = 10
    xp_bonus_completion: int = 50
    xp_penalty_hint: int = 5

    # Server Settings
    workers: int = 4
    host: str = "0.0.0.0"
    port: int = 8000

    # Security
    max_request_size: int = 10 * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


def validate_production_settings(settings: Settings) -> None:
    """Validate settings for production deployment."""
    if settings.is_production:
        if "change" in settings.secret_key.lower() or settings.secret_key == "your-super-secret-key-change-in-production":
            raise ValueError("⚠️ SECURITY ERROR: Cannot use default SECRET_KEY in production!")

        if settings.is_sqlite:
            warnings.warn("⚠️ SQLite is not recommended for production.", UserWarning)

        if settings.debug:
            warnings.warn("⚠️ DEBUG mode is enabled in production.", UserWarning)


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

try:
    validate_production_settings(settings)
except ValueError:
    if settings.is_production:
        raise
