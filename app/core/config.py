from functools import lru_cache
from typing import Optional
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    environment: str = "development"
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = Field(
        default=8000,
        validation_alias=AliasChoices("PORT", "port"),
    )
    rate_limit_per_minute: int = 60

    # Database
    database_url: str = "sqlite+aiosqlite:///./vetta.db"

    # Cache & Tasks
    use_celery: bool = False
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # LLM Provider
    google_api_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("GOOGLE_API_KEY", "GEMINI_API_KEY", "google_api_key"),
    )
    llm_model: str = "gemini-3.6-flash"

    # AWS S3 Storage
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    aws_s3_bucket: Optional[str] = None
    aws_s3_endpoint_url: Optional[str] = None
    local_storage_dir: str = "./storage_uploads"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def is_s3_configured(self) -> bool:
        return bool(
            self.aws_access_key_id
            and self.aws_secret_access_key
            and self.aws_s3_bucket
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
