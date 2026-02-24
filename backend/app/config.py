"""Application configuration using Pydantic Settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All application settings, loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://acras:acras@postgres:5432/acras"
    DATABASE_SYNC_URL: str = "postgresql://acras:acras@postgres:5432/acras"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

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
    OPENWEATHER_API_KEY: str = ""
    WEATHER_CACHE_TTL_SECONDS: int = 600

    # Alerts
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""

    # Frontend
    NEXT_PUBLIC_API_URL: str = "http://localhost:8000"
    NEXT_PUBLIC_WS_URL: str = "ws://localhost:8000/api/v1/ws"

    # Monitoring
    PROMETHEUS_ENABLED: bool = True
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
