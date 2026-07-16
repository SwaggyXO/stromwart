import os
from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_ROOT = Path(__file__).resolve().parents[2]


class LlmProvider(StrEnum):
    DISABLED = "disabled"
    OPENAI_COMPATIBLE = "openai_compatible"
    ANTHROPIC = "anthropic"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        env_prefix="STROMWART_",
        extra="ignore",
    )

    environment: str = "development"
    database_url: str = (
        "postgresql+asyncpg://stromwart:stromwart@localhost:5434/stromwart"
    )
    cors_origins: str = "http://localhost:5173"
    llm_provider: LlmProvider = LlmProvider.DISABLED
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_model: str | None = None
    llm_timeout_seconds: float = Field(default=30, gt=0, le=120)
    hf_token: str | None = None

    def model_post_init(self, __context: object) -> None:
        token = self.hf_token or os.environ.get("HUGGINGFACE_HUB_TOKEN")
        if token:
            os.environ.setdefault("HUGGINGFACE_HUB_TOKEN", token)

    @property
    def allowed_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
