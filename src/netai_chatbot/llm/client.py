"""LLM API client supporting NRP's managed models via OpenAI-compatible interface."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import ClassVar

import httpx

from netai_chatbot.config import LLMModel, Settings, get_settings
from netai_chatbot.utils import get_logger

logger = get_logger(__name__)


@dataclass
class LLMResponse:
    """Structured response from the LLM service."""

    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"


class LLMClient:
    """OpenAI-compatible API client for NRP's managed LLM service.

    Supports Qwen3-VL, GLM-4.7, and GPT-OSS models available through
    the National Research Platform's LLM inference endpoints.
    """

    # Model-specific parameters for optimal network diagnostics performance
    MODEL_CONFIGS: ClassVar[dict[str, dict]] = {
        LLMModel.QWEN3_VL: {
            "description": "Qwen3-VL — strong reasoning for complex network analysis",
            "supports_vision": True,
            "optimal_temperature": 0.7,
        },
        LLMModel.GLM_4_7: {
            "description": "GLM-4.7 — fast inference for real-time diagnostics",
            "supports_vision": False,
            "optimal_temperature": 0.6,
        },
        LLMModel.GPT_OSS: {
            "description": "GPT-OSS — balanced performance for general queries",
            "supports_vision": False,
            "optimal_temperature": 0.7,
        },
    }

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client = httpx.AsyncClient(
            base_url=self.settings.llm_api_base_url,
            headers={
                "Authorization": f"Bearer {self.settings.llm_api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(60.0, connect=10.0),
        )

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: LLMModel | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stream: bool = False,
    ) -> LLMResponse:
        """Send a chat completion request to the NRP LLM service.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            model: LLM model to use (defaults to settings).
            temperature: Sampling temperature (defaults to settings).
            max_tokens: Maximum response tokens (defaults to settings).
            stream: Whether to stream the response.

        Returns:
            LLMResponse with the model's reply.
        """
        model = model or self.settings.llm_default_model
        temperature = temperature or self.settings.llm_temperature
        max_tokens = max_tokens or self.settings.llm_max_tokens

        payload = {
            "model": model.value if isinstance(model, LLMModel) else model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        logger.info(
            "llm_request",
            model=payload["model"],
            message_count=len(messages),
            max_tokens=max_tokens,
        )

        try:
            response = await self._client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            choice = data["choices"][0]
            return LLMResponse(
                content=choice["message"]["content"],
                model=data.get("model", payload["model"]),
                usage=data.get("usage", {}),
                finish_reason=choice.get("finish_reason", "stop"),
            )
        except httpx.HTTPStatusError as e:
            logger.error("llm_api_error", status=e.response.status_code, detail=str(e))
            raise
        except httpx.RequestError as e:
            logger.error("llm_connection_error", detail=str(e))
            raise

    async def stream_completion(
        self,
        messages: list[dict[str, str]],
        model: LLMModel | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """Stream a chat completion response token by token.

        Yields:
            Individual content tokens as they are generated.
        """
        model = model or self.settings.llm_default_model
        payload = {
            "model": model.value if isinstance(model, LLMModel) else model,
            "messages": messages,
            "temperature": temperature or self.settings.llm_temperature,
            "max_tokens": max_tokens or self.settings.llm_max_tokens,
            "stream": True,
        }

        async with self._client.stream("POST", "/chat/completions", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    chunk = json.loads(line[6:])
                    delta = chunk["choices"][0].get("delta", {})
                    if content := delta.get("content"):
                        yield content

    def get_model_info(self, model: LLMModel | None = None) -> dict:
        """Get configuration info for a specific model."""
        model = model or self.settings.llm_default_model
        return {
            "model": model.value,
            **self.MODEL_CONFIGS.get(model, {}),
        }

    def list_models(self) -> list[dict]:
        """List all available NRP LLM models with their configurations."""
        return [{"model": m.value, **self.MODEL_CONFIGS[m]} for m in LLMModel]

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()


class MockLLMClient(LLMClient):
    """Mock LLM client for testing and demo purposes.

    Returns pre-built responses that simulate real LLM behavior
    for network diagnostics queries.
    """

    MOCK_RESPONSES: ClassVar[dict[str, str]] = {
        "throughput": (
            "## Throughput Analysis\n\n"
            "Based on the current network telemetry data, I've identified the following:\n\n"
            "- **Current throughput**: 8.2 Gbps (expected: 10 Gbps)\n"
            "- **Degradation**: ~18% below baseline\n"
            "- **Affected path**: Chicago → Denver segment\n\n"
            "### Likely Causes\n"
            "1. **Link congestion** on the Chicago-Denver backbone during peak hours\n"
            "2. **MTU mismatch** detected at hop 4 (router-chi-02)\n\n"
            "### Recommended Actions\n"
            "- Check interface counters on router-chi-02 for CRC errors\n"
            "- Verify MTU settings along the path (should be 9000 for jumbo frames)\n"
            "- Consider traffic engineering to redistribute load\n"
        ),
        "latency": (
            "## Latency Analysis\n\n"
            "The latency measurements show:\n\n"
            "- **Current RTT**: 45ms (baseline: 28ms)\n"
            "- **Jitter**: 12ms (elevated, baseline: 3ms)\n"
            "- **Packet loss**: 0.3%\n\n"
            "### Root Cause Analysis\n"
            "The increased latency correlates with a routing change detected at 14:32 UTC. "
            "Traffic is now traversing an additional hop through the Kansas City exchange point.\n\n"
            "### Recommendations\n"
            "- Review BGP route advertisements from AS64512\n"
            "- Check if the primary path (direct Chicago-Denver) has been withdrawn\n"
            "- Monitor for route flapping on the affected prefix\n"
        ),
        "anomaly": (
            "## Anomaly Detection Report\n\n"
            "🔴 **Anomaly detected** on the San Diego ↔ Seattle path\n\n"
            "### Details\n"
            "- **Type**: Intermittent packet loss burst\n"
            "- **Severity**: High (4.2% packet loss, threshold: 1%)\n"
            "- **Duration**: Started 2 hours ago, ongoing\n"
            "- **Pattern**: Loss occurs in 30-second bursts every ~5 minutes\n\n"
            "### Correlated Events\n"
            "- Interface flapping detected on `xe-0/0/1` at hop 6\n"
            "- Optical power levels marginal (-18.2 dBm, threshold: -20 dBm)\n\n"
            "### Suggested Remediation\n"
            "1. **Immediate**: Contact NOC to inspect fiber optic connections at hop 6\n"
            "2. **Short-term**: Reroute traffic via alternate path through Portland\n"
            "3. **Long-term**: Schedule fiber cleaning/replacement for the affected span\n"
        ),
        "default": (
            "## Network Diagnostics Assistant\n\n"
            "I can help you with:\n\n"
            "- **Throughput analysis** — Identify bandwidth bottlenecks and degradation\n"
            "- **Latency diagnostics** — Analyze RTT, jitter, and routing issues\n"
            "- **Anomaly detection** — Detect and explain unusual network behavior\n"
            "- **Traceroute analysis** — Examine network paths and identify problematic hops\n"
            "- **Remediation strategies** — Get actionable recommendations for network issues\n\n"
            "Ask me about any network performance concern and I'll analyze the available "
            "telemetry data to provide insights and recommendations.\n"
        ),
    }

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        model: LLMModel | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stream: bool = False,
    ) -> LLMResponse:
        """Return mock responses based on message content keywords."""
        last_message = messages[-1]["content"].lower() if messages else ""

        response_key = "default"
        for key in self.MOCK_RESPONSES:
            if key in last_message:
                response_key = key
                break

        return LLMResponse(
            content=self.MOCK_RESPONSES[response_key],
            model=(model or self.settings.llm_default_model).value,
            usage={"prompt_tokens": 150, "completion_tokens": 300, "total_tokens": 450},
            finish_reason="stop",
        )
