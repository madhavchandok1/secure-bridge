from functools import lru_cache

from pydantic import Field
from pydantic_settings import (
    BaseSettings, 
    SettingsConfigDict
)

class Settings(BaseSettings):
    """
    Centralized configuration management for the application.

    This class automatically loads and validates environment variables from the 
    system environment or a local .env file. It uses Pydantic for strict 
    type enforcement and provides default values for non-sensitive settings.
    """

    # Pydantic configuration for environment variable loading
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore" # Discards extra environment variables not defined in this class
    )

    # General Application Metadata
    APP_NAME: str = "Secure Deal Room"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"

    # Database Infrastructure
    DATABASE_URL: str

    # Supabase Integration (Auth & Database Services)
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_KEY: str

    # Authentication & Security Settings
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Cryptography: Used for at-rest data encryption
    FERNET_SECRET_KEY: str

    # Storage Infrastructure
    STORAGE_BUCKET_NAME: str

    # CORS Configuration: List of allowed origins for cross-site requests
    BACKEND_CORS_ORIGINS: list[str] = Field(default_factory=list)

    # Operational Constraints
    MAX_FILE_SIZE_MB: int = 100

    # Rate Limiting: Prevent brute-force attacks on auth endpoints
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_REGISTER: str = "3/minute"

@lru_cache
def get_settings() -> Settings:
    """
    Factory function that returns a cached instance of the Settings class.

    Using @lru_cache ensures that the .env file is read and validated only once, 
    significantly improving performance across multiple imports.

    Returns:
        Settings: A singleton-like instance of the application configuration.
    """

    return Settings()

settings = get_settings()