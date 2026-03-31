"""Application settings and configuration."""

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    service_name: str = "app"
    environment: str = "development"
    log_level: str = "INFO"

    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_database: str = "app"
    postgres_min_pool_size: int = 5
    postgres_max_pool_size: int = 20

    # AWS
    aws_region: str = "us-east-1"
    aws_endpoint_url: str | None = None  # For local testing with LocalStack
    use_localstack: bool = False

    @model_validator(mode="after")
    def detect_localstack(self) -> "Settings":
        """Auto-detect LocalStack if endpoint URL is set."""
        # Auto-detect LocalStack if endpoint URL is set or use_localstack is True
        if self.use_localstack or (self.aws_endpoint_url is not None):
            self.use_localstack = True
        return self

    # Event queue URLs - one per event type
    event_topic_arn: str = ""
    event_queue_url: str = ""

    model_config = SettingsConfigDict(
        env_file=[".env.local", ".env"],  # Load .env.local first, then .env (later files override earlier ones)
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
