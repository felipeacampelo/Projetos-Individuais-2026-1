from __future__ import annotations

import os
from functools import lru_cache

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class Settings(BaseModel):
    """Typed application settings loaded from environment variables."""

    model_config = ConfigDict(frozen=True)

    app_env: str = Field(default="development")
    app_name: str = Field(default="pipeline-uda-ri-habitacional")
    app_version: str = Field(default="0.1.0")
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/pipeline_uda"
    )
    llm_provider: str = Field(default="openai")
    llm_api_key: str = Field(default="")
    polling_enabled: bool = Field(default=False)
    polling_interval_minutes: int = Field(default=1440, ge=1)
    normalization_knowledge_version: str = Field(default="1.0.0")
    semantic_contract_version: str = Field(default="1.0.0")

    @classmethod
    def from_env(cls) -> "Settings":
        raw = {
            "app_env": os.getenv("APP_ENV", "development"),
            "app_name": os.getenv("APP_NAME", "pipeline-uda-ri-habitacional"),
            "app_version": os.getenv("APP_VERSION", "0.1.0"),
            "database_url": os.getenv(
                "DATABASE_URL",
                "postgresql+psycopg://postgres:postgres@localhost:5432/pipeline_uda",
            ),
            "llm_provider": os.getenv("LLM_PROVIDER", "openai"),
            "llm_api_key": os.getenv("LLM_API_KEY", ""),
            "polling_enabled": os.getenv("POLLING_ENABLED", "false"),
            "polling_interval_minutes": os.getenv("POLLING_INTERVAL_MINUTES", "1440"),
            "normalization_knowledge_version": os.getenv(
                "NORMALIZATION_KNOWLEDGE_VERSION",
                "1.0.0",
            ),
            "semantic_contract_version": os.getenv("SEMANTIC_CONTRACT_VERSION", "1.0.0"),
        }
        return cls.model_validate(raw)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    try:
        return Settings.from_env()
    except ValidationError as exc:
        raise RuntimeError("Invalid application settings") from exc
