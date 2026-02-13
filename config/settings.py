# config/settings.py

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # -----------------------------
    # Azure OpenAI Configuration
    # -----------------------------
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_DEPLOYMENT_NAME: str
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"

    # -----------------------------
    # Service Endpoints
    # -----------------------------
    ASSESSMENT_API_URL: str
    PARSING_API_URL: str
    MAPPING_API_URL: str
    COSMOSDB_API_URL: str
    MONITORING_AGENT_URL: str

    # -----------------------------
    # General Configuration
    # -----------------------------
    REQUEST_TIMEOUT: float
    CORS_ORIGINS: str = "*"

    # -----------------------------
    # Batch / Parallel Processing
    # -----------------------------
    # Maximum number of workbooks processed in parallel
    MAX_CONCURRENT_WORKBOOKS: int = 3

    # Small delay (seconds) added before each task starts
    # Prevents all bots from firing at the exact same time
    START_JITTER_SECONDS: float = 0.25

    # -----------------------------
    # Pydantic Settings Config
    # -----------------------------
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
