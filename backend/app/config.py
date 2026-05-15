from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "Secure Deal Room"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str

    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_KEY: str

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    FERNET_SECRET_KEY: str

    STORAGE_BUCKET_NAME: str

    BACKEND_CORS_ORIGINS: list[str] = Field(default_factory=list)

    MAX_FILE_SIZE_MB: int = 100

    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_REGISTER: str = "3/minute"

@lru_cache
def get_settings() -> Settings:
    """
    Returns cached application settings.
    """

    return Settings()

settings = get_settings()