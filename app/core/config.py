"""
Application configuration with production-ready settings.

Supports both development (SQLite) and production (PostgreSQL) environments.
Includes connection pooling for high-concurrency game scenarios.
"""

from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache
import warnings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    app_name: str = "EdTech Word Chain API"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"  # development, staging, production

    # Database (SQLite for development, switch to PostgreSQL for production)
    # SQLite: sqlite+aiosqlite:///./data/wordchain.db
    # PostgreSQL: postgresql+asyncpg://user:password@localhost:5432/wordchain_db
    database_url: str = "sqlite+aiosqlite:///./data/wordchain.db"

    # Database Connection Pool Settings (for PostgreSQL)
    # Optimized for game concurrency - many simultaneous connections
    db_pool_size: int = 20  # Base persistent connections
    db_max_overflow: int = 30  # Extra connections for peak load (total: 50)
    db_pool_timeout: int = 30  # Seconds to wait for connection

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT Authentication
    secret_key: str = "your-super-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Password Reset
    password_reset_token_expire_minutes: int = 60
    email_verification_token_expire_hours: int = 24

    # Mailjet Email Settings
    mailjet_api_key: Optional[str] = None
    mailjet_api_secret: Optional[str] = None
    mailjet_sender_email: str = "noreply@example.com"
    mailjet_sender_name: str = "EdTech Word Chain"

    # Frontend URL (for email links)
    frontend_url: str = "http://localhost:3000"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Game Settings
    min_word_length: int = 3
    max_word_length: int = 6
    default_game_mode: str = "STANDARD"

    # XP Settings
    xp_per_valid_move: int = 10
    xp_bonus_completion: int = 50
    xp_penalty_hint: int = 5

    # Production Server Settings
    workers: int = 4  # Number of uvicorn/gunicorn workers
    host: str = "0.0.0.0"
    port: int = 8000

    # Security Settings
    max_request_size: int = 10 * 1024 * 1024  # 10MB max request size

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite database."""
        return self.database_url.startswith("sqlite")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def validate_production_settings(settings: Settings) -> None:
    """
    Validate settings for production deployment.
    Raises warnings for insecure configurations.
    """
    if settings.is_production:
        # Check for default secret key
        if "change" in settings.secret_key.lower() or settings.secret_key == "your-super-secret-key-change-in-production":
            raise ValueError(
                "⚠️  SECURITY ERROR: Cannot use default SECRET_KEY in production! "
                "Generate a secure key with: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
            )

        # Warn about SQLite in production
        if settings.is_sqlite:
            warnings.warn(
                "⚠️  SQLite is not recommended for production. "
                "Consider switching to PostgreSQL for better concurrency.",
                UserWarning
            )

        # Warn about debug mode
        if settings.debug:
            warnings.warn(
                "⚠️  DEBUG mode is enabled in production. This may expose sensitive information.",
                UserWarning
            )


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


settings = get_settings()

# Validate on import (only raises error in production with insecure settings)
try:
    validate_production_settings(settings)
except ValueError as e:
    if settings.is_production:
        raise
    else:
        # In development, just warn
        pass
