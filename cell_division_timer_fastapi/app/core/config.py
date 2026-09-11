"""Application settings and environment configuration."""

from functools import lru_cache
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application settings loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ============================================================
    # Core Application Info
    # ============================================================

    APP_NAME: str = "Cell Division Timer API"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # API Configuration
    API_PREFIX: str = "/api/v1"
    API_V1_PREFIX: str = "/api/v1"
    API_V2_PREFIX: str = "/api/v2"

    DEFAULT_API_VERSION: str = "v1"
    SUPPORTED_API_VERSIONS: List[str] = ["v1", "v2-beta"]

    # ============================================================
    # Server Configuration
    # ============================================================

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ============================================================
    # Database Configuration
    # ============================================================

    # SQLite for local development/testing
    # PostgreSQL can be supplied through DATABASE_URL in production
    DATABASE_URL: str = "sqlite:///./cell_division.db"

    DB_ECHO: bool = False

    # ============================================================
    # Security & CORS
    # ============================================================

    CORS_ORIGINS: List[str] = ["*"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(
        cls,
        v: Union[str, List[str]],
    ) -> List[str]:
        """Convert comma-separated or JSON CORS origins into a list."""

        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json

                try:
                    return json.loads(v)
                except Exception:
                    pass

            return [
                origin.strip()
                for origin in v.split(",")
                if origin.strip()
            ]

        if isinstance(v, list):
            return v

        return ["*"]

    # ============================================================
    # NCBI / PubMed Configuration
    # ============================================================

    # NCBI E-utilities API key.
    #
    # IMPORTANT:
    # Do NOT hard-code the actual key here.
    # Store it in the .env file.
    NCBI_API_KEY: str = ""

    # Identifier for your application when making NCBI requests.
    NCBI_TOOL: str = "cell_division_timer"

    # Contact email recommended by NCBI for E-utilities requests.
    NCBI_EMAIL: str = ""

    # NCBI E-utilities base URL.
    NCBI_BASE_URL: str = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    )

    # Maximum number of PubMed records requested per search.
    NCBI_DEFAULT_RETMAX: int = 10

    # HTTP timeout for NCBI requests, in seconds.
    NCBI_TIMEOUT: float = 30.0

    # ============================================================
    # Logging
    # ============================================================

    LOG_LEVEL: str = "INFO"


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings instance."""

    return Settings()