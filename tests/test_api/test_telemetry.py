"""Tests for network telemetry API endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_network_summary(async_client: AsyncClient) -> None:
    """Test network health summary endpoint."""
    response = await async_client.get("/api/v1/network/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_paths" in data
    assert "healthy" in data
    assert "degraded" in data
    assert "warning" in data
    assert "critical" in data
    assert "paths" in data
    assert isinstance(data["paths"], list)


@pytest.mark.asyncio
async def test_path_diagnostics(async_client: AsyncClient) -> None:
    """Test path-specific diagnostics endpoint."""
    response = await async_client.post(
        "/api/v1/network/diagnostics",
        json={
            "source": "sdsc-prp.ucsd.edu",
            "destination": "nrp-chi.uchicago.edu",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "path" in data
    assert "traceroute" in data
    assert "anomalies" in data
    assert "measurement_count" in data


@pytest.mark.asyncio
async def test_run_traceroute(async_client: AsyncClient) -> None:
    """Test traceroute execution endpoint."""
    response = await async_client.post(
        "/api/v1/network/traceroute",
        json={
            "source": "sdsc-prp.ucsd.edu",
            "destination": "nrp-chi.uchicago.edu",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "sdsc-prp.ucsd.edu"
    assert data["destination"] == "nrp-chi.uchicago.edu"
    assert "hops" in data
    assert len(data["hops"]) > 0
    assert "hop_count" in data


@pytest.mark.asyncio
async def test_list_nodes(async_client: AsyncClient) -> None:
    """Test listing NRP network nodes."""
    response = await async_client.get("/api/v1/network/nodes")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "count" in data
    assert data["count"] > 0
    assert "sdsc-prp.ucsd.edu" in data["nodes"]


@pytest.mark.asyncio
async def test_path_health(async_client: AsyncClient) -> None:
    """Test specific path health endpoint."""
    response = await async_client.get(
        "/api/v1/network/paths/sdsc-prp.ucsd.edu/nrp-chi.uchicago.edu"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "sdsc-prp.ucsd.edu"
    assert data["destination"] == "nrp-chi.uchicago.edu"
    assert "throughput_gbps" in data
    assert "latency_ms" in data
    assert "health_status" in data
