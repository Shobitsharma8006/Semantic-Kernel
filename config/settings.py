# config/settings.py

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API Keys & Base URLs (Required)
    OPENROUTER_API_KEY: str
    OPENROUTER_BASE_URL: str

    # Service Endpoints (Required)
    ASSESSMENT_API_URL: str
    PARSING_API_URL: str
    MAPPING_API_URL: str

    # Configuration (Required)
    REQUEST_TIMEOUT: float

    model_config = SettingsConfigDict(
        # This tells Pydantic to read the .env file from the project root
        env_file=Path(__file__).parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()