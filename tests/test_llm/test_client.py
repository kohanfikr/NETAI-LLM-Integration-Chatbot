"""Tests for LLM client."""

from __future__ import annotations

import pytest

from netai_chatbot.config import LLMModel
from netai_chatbot.llm.client import LLMResponse, MockLLMClient


@pytest.mark.asyncio
async def test_mock_client_default_response(mock_llm_client: MockLLMClient) -> None:
    """Test mock client returns default response for generic queries."""
    messages = [{"role": "user", "content": "Hello, what can you do?"}]
    response = await mock_llm_client.chat_completion(messages)

    assert isinstance(response, LLMResponse)
    assert len(response.content) > 0
    assert "Network Diagnostics Assistant" in response.content
    assert response.finish_reason == "stop"


@pytest.mark.asyncio
async def test_mock_client_throughput_response(mock_llm_client: MockLLMClient) -> None:
    """Test mock client returns throughput-specific response."""
    messages = [{"role": "user", "content": "What is the current throughput?"}]
    response = await mock_llm_client.chat_completion(messages)

    assert "Throughput" in response.content
    assert "Gbps" in response.content


@pytest.mark.asyncio
async def test_mock_client_latency_response(mock_llm_client: MockLLMClient) -> None:
    """Test mock client returns latency-specific response."""
    messages = [{"role": "user", "content": "Check the latency"}]
    response = await mock_llm_client.chat_completion(messages)

    assert "Latency" in response.content
    assert "RTT" in response.content


@pytest.mark.asyncio
async def test_mock_client_anomaly_response(mock_llm_client: MockLLMClient) -> None:
    """Test mock client returns anomaly-specific response."""
    messages = [{"role": "user", "content": "Are there any anomaly detected?"}]
    response = await mock_llm_client.chat_completion(messages)

    assert "Anomaly" in response.content


@pytest.mark.asyncio
async def test_mock_client_model_override(mock_llm_client: MockLLMClient) -> None:
    """Test mock client respects model override."""
    messages = [{"role": "user", "content": "test"}]
    response = await mock_llm_client.chat_completion(messages, model=LLMModel.GLM_4_7)
    assert response.model == "glm-4.7"


@pytest.mark.asyncio
async def test_mock_client_usage_stats(mock_llm_client: MockLLMClient) -> None:
    """Test mock client returns usage statistics."""
    messages = [{"role": "user", "content": "test"}]
    response = await mock_llm_client.chat_completion(messages)

    assert "prompt_tokens" in response.usage
    assert "completion_tokens" in response.usage
    assert "total_tokens" in response.usage


def test_list_models(mock_llm_client: MockLLMClient) -> None:
    """Test listing available models."""
    models = mock_llm_client.list_models()
    assert len(models) == 3
    model_names = {m["model"] for m in models}
    assert model_names == {"qwen3-vl", "glm-4.7", "gpt-oss"}


def test_get_model_info(mock_llm_client: MockLLMClient) -> None:
    """Test getting model info."""
    info = mock_llm_client.get_model_info(LLMModel.QWEN3_VL)
    assert info["model"] == "qwen3-vl"
    assert info["supports_vision"] is True

    info = mock_llm_client.get_model_info(LLMModel.GLM_4_7)
    assert info["model"] == "glm-4.7"
    assert info["supports_vision"] is False
