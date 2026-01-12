# config/settings.py

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # OpenRouter (required)
    OPENROUTER_API_KEY: str = "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"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"   # ← add this line!

    # Assessment API
    ASSESSMENT_API_URL: str = "http://0.0.0.0:5001/api/assessment"

    # Optional timeouts etc.
    REQUEST_TIMEOUT: float = 60.0

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()