"""
Application configuration.

Defaults are provided for local development convenience only.
Production must inject environment variables.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

    # Environment
    # development: local/dev usage (prints mock verification codes to stdout)
    # production: production usage (requires secure configuration)
    # test: used by unit tests (skips external connections)
    APP_ENV: str = Field(default="development", validation_alias="APP_ENV")

    # Admin bootstrap / safety checks
    # Used only for production safety validation (do not store plaintext passwords in code in real systems).
    ADMIN_PASSWORD: str = Field(default="admin123", validation_alias="ADMIN_PASSWORD")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql://membership:membership123@localhost:5432/membership_db",
        validation_alias="DATABASE_URL",
    )

    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379/0", validation_alias="REDIS_URL")

    # JWT
    JWT_SECRET_KEY: str = Field(default="your-secret-key-change-in-production", validation_alias="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    JWT_EXPIRY_HOURS: int = Field(default=2, validation_alias="JWT_EXPIRY_HOURS")

    # Rate Limiting
    VERIFICATION_CODE_RATE_LIMIT_MINUTE: int = Field(default=1, validation_alias="VERIFICATION_CODE_RATE_LIMIT_MINUTE")
    VERIFICATION_CODE_RATE_LIMIT_DAY: int = Field(default=10, validation_alias="VERIFICATION_CODE_RATE_LIMIT_DAY")
    LOGIN_FAILURE_LIMIT: int = Field(default=5, validation_alias="LOGIN_FAILURE_LIMIT")
    LOGIN_LOCK_MINUTES: int = Field(default=15, validation_alias="LOGIN_LOCK_MINUTES")

    # Verification Code
    VERIFICATION_CODE_LENGTH: int = Field(default=6, validation_alias="VERIFICATION_CODE_LENGTH")
    VERIFICATION_CODE_EXPIRY_MINUTES: int = Field(default=5, validation_alias="VERIFICATION_CODE_EXPIRY_MINUTES")


settings = Settings()
