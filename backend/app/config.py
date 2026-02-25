"""Application configuration using Pydantic Settings."""

from pathlib import Path

from pydantic_settings import BaseSettings

# Resolve .env from project root (one level above backend/)
_env_file = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    """All application settings, loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://acras:acras@localhost:5433/acras"
    DATABASE_SYNC_URL: str = "postgresql://acras:acras@localhost:5433/acras"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_KEY: str = "dev-secret-key-change-in-production"
    CORS_ORIGINS: str = "http://localhost:3000"

    # ML Models
    YOLO_MODEL_PATH: str = "yolov8s.pt"
    YOLO_CONFIDENCE_THRESHOLD: float = 0.5
    CRASH_CLASSIFIER_PATH: str = "models/crash_classifier.pt"
    CRASH_CONFIDENCE_THRESHOLD: float = 0.7
    SEVERITY_MODEL_PATH: str = "models/severity_model.pt"

    # Processing
    FRAME_EXTRACTION_FPS: int = 1
    MAX_CONCURRENT_CAMERAS: int = 100
    FRAME_BUFFER_SIZE: int = 100

    # Weather
    WEATHER_CACHE_TTL_SECONDS: int = 600
    WEATHER_CACHE_MAX_SIZE: int = 1000

    # Alerts
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""

    # Monitoring
    PROMETHEUS_ENABLED: bool = True
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def async_database_url(self) -> str:
        """Return an asyncpg-compatible DATABASE_URL."""
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def sync_database_url(self) -> str:
        """Return a psycopg2-compatible DATABASE_URL."""
        url = self.DATABASE_SYNC_URL or self.DATABASE_URL
        if "+asyncpg" in url:
            url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
        return url

    model_config = {"env_file": str(_env_file), "env_file_encoding": "utf-8"}


settings = Settings()
