"""Tests for health check and info endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient) -> None:
    """Test liveness probe endpoint."""
    response = await async_client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_readiness_check(async_client: AsyncClient) -> None:
    """Test readiness probe endpoint."""
    response = await async_client.get("/readyz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "version" in data


@pytest.mark.asyncio
async def test_service_info(async_client: AsyncClient) -> None:
    """Test service info endpoint."""
    response = await async_client.get("/api/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "NETAI Chatbot"
    assert "version" in data
    assert "available_models" in data
    assert len(data["available_models"]) == 3
    assert "endpoints" in data

    # Verify all model IDs
    model_ids = {m["id"] for m in data["available_models"]}
    assert model_ids == {"qwen3-vl", "glm-4.7", "gpt-oss"}
