from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "LinkPulse URL Analytics"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    PUBLIC_BASE_URL: str = "http://localhost:8000"
    SECRET_KEY: SecretStr = SecretStr("dev-only-change-me")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60, ge=1, le=1440)
    DATABASE_URL: str = "sqlite:///./linkpulse.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_CAPACITY: int = Field(default=60, ge=1)
    RATE_LIMIT_REFILL_PER_SECOND: float = Field(default=1.0, gt=0)
    RATE_LIMIT_FAIL_OPEN: bool = True
    GEOIP_DB_PATH: str | None = None
    S3_BUCKET: str | None = None
    AWS_REGION: str = "ap-south-1"

    @field_validator("PUBLIC_BASE_URL")
    @classmethod
    def strip_trailing_slash(cls, value: str) -> str:
        return value.rstrip("/")

    @field_validator("SECRET_KEY")
    @classmethod
    def require_secure_secret_in_production(cls, value: SecretStr, info):
        environment = info.data.get("ENVIRONMENT", "development")
        if environment == "production" and len(value.get_secret_value()) < 32:
            raise ValueError("SECRET_KEY must contain at least 32 characters in production")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
