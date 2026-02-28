"""LLM provider configurations for NRP's managed models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderConfig:
    """Configuration for an LLM provider/model endpoint."""

    name: str
    model_id: str
    description: str
    max_context_length: int
    supports_streaming: bool = True
    supports_vision: bool = False
    recommended_for: list[str] | None = None


# NRP Managed LLM Service providers
NRP_PROVIDERS: dict[str, ProviderConfig] = {
    "qwen3-vl": ProviderConfig(
        name="Qwen3-VL",
        model_id="qwen3-vl",
        description=(
            "Multimodal model with vision capabilities. Excellent for analyzing "
            "network topology diagrams and visual representations of network data."
        ),
        max_context_length=32768,
        supports_vision=True,
        recommended_for=[
            "topology visualization analysis",
            "network diagram interpretation",
            "complex multi-step reasoning",
        ],
    ),
    "glm-4.7": ProviderConfig(
        name="GLM-4.7",
        model_id="glm-4.7",
        description=(
            "Fast inference model optimized for real-time interactions. "
            "Best suited for quick network diagnostics queries."
        ),
        max_context_length=16384,
        recommended_for=[
            "real-time diagnostics",
            "quick Q&A",
            "streaming responses",
        ],
    ),
    "gpt-oss": ProviderConfig(
        name="GPT-OSS",
        model_id="gpt-oss",
        description=(
            "Open-source GPT model with balanced performance. "
            "Good all-around choice for network diagnostics assistance."
        ),
        max_context_length=16384,
        recommended_for=[
            "general network queries",
            "remediation strategies",
            "documentation generation",
        ],
    ),
}


def get_provider(model_id: str) -> ProviderConfig | None:
    """Get provider configuration by model ID."""
    return NRP_PROVIDERS.get(model_id)


def list_providers() -> list[ProviderConfig]:
    """List all available NRP LLM providers."""
    return list(NRP_PROVIDERS.values())
