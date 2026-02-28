"""Application configuration using pydantic-settings."""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMModel(StrEnum):
    """Supported LLM models available through NRP's managed service."""

    QWEN3_VL = "qwen3-vl"
    GLM_4_7 = "glm-4.7"
    GPT_OSS = "gpt-oss"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # LLM Configuration
    llm_api_base_url: str = Field(
        default="https://llm.nrp-nautilus.io/v1",
        description="NRP LLM Service endpoint (OpenAI-compatible)",
    )
    llm_api_key: str = Field(
        default="mock-key-for-development",
        description="API key for NRP LLM service",
    )
    llm_default_model: LLMModel = Field(
        default=LLMModel.QWEN3_VL,
        description="Default LLM model to use",
    )
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    llm_max_tokens: int = Field(default=2048, ge=1, le=8192)

    # Application
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    app_debug: bool = Field(default=False)
    app_log_level: str = Field(default="info")

    # Network Diagnostics
    perfsonar_url: str = Field(default="http://perfsonar.example.com")
    perfsonar_api_key: str = Field(default="")
    enable_mock_data: bool = Field(
        default=True,
        description="Use simulated perfSONAR data for demo/development",
    )

    # Context & Memory
    max_conversation_history: int = Field(default=50)
    context_window_size: int = Field(default=10)


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings singleton."""
    return Settings()
