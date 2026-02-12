from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://membership:membership123@localhost:5432/membership_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 2

    # Rate Limiting
    VERIFICATION_CODE_RATE_LIMIT_MINUTE: int = 1
    VERIFICATION_CODE_RATE_LIMIT_DAY: int = 10
    LOGIN_FAILURE_LIMIT: int = 5
    LOGIN_LOCK_MINUTES: int = 15

    # Verification Code
    VERIFICATION_CODE_LENGTH: int = 6
    VERIFICATION_CODE_EXPIRY_MINUTES: int = 5

    # SMTP
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
