"""Tests for perfSONAR data integration."""

from __future__ import annotations

from datetime import UTC

import pytest

from netai_chatbot.diagnostics.perfsonar import (
    NRP_NODES,
    MeasurementType,
    NetworkPath,
    PerfSONARClient,
    PerfSONARMeasurement,
)


@pytest.mark.asyncio
async def test_get_throughput(perfsonar_client: PerfSONARClient) -> None:
    """Test retrieving throughput measurements."""
    measurements = await perfsonar_client.get_throughput(
        "sdsc-prp.ucsd.edu", "nrp-chi.uchicago.edu", time_range_hours=6
    )
    assert len(measurements) > 0
    assert all(isinstance(m, PerfSONARMeasurement) for m in measurements)
    assert all(m.test_type == MeasurementType.THROUGHPUT for m in measurements)
    assert all(m.unit == "Gbps" for m in measurements)
    assert all(m.value > 0 for m in measurements)


@pytest.mark.asyncio
async def test_get_latency(perfsonar_client: PerfSONARClient) -> None:
    """Test retrieving latency measurements."""
    measurements = await perfsonar_client.get_latency(
        "sdsc-prp.ucsd.edu", "nrp-chi.uchicago.edu", time_range_hours=1
    )
    assert len(measurements) > 0
    assert all(m.test_type == MeasurementType.LATENCY for m in measurements)
    assert all(m.unit == "ms" for m in measurements)


@pytest.mark.asyncio
async def test_get_network_paths(perfsonar_client: PerfSONARClient) -> None:
    """Test retrieving all monitored network paths."""
    paths = await perfsonar_client.get_network_paths()
    assert len(paths) > 0
    assert all(isinstance(p, NetworkPath) for p in paths)
    for path in paths:
        assert path.health_status in ("healthy", "warning", "degraded", "critical")


@pytest.mark.asyncio
async def test_get_path_health(perfsonar_client: PerfSONARClient) -> None:
    """Test getting health for a specific path."""
    path = await perfsonar_client.get_path_health("sdsc-prp.ucsd.edu", "nrp-chi.uchicago.edu")
    assert isinstance(path, NetworkPath)
    assert path.source == "sdsc-prp.ucsd.edu"
    assert path.destination == "nrp-chi.uchicago.edu"
    assert path.throughput_gbps is not None
    assert path.latency_ms is not None


def test_network_path_health_status() -> None:
    """Test NetworkPath health classification logic."""
    healthy = NetworkPath(
        source="a",
        destination="b",
        throughput_gbps=8.0,
        latency_ms=20.0,
        packet_loss_pct=0.0,
    )
    assert healthy.health_status == "healthy"

    degraded = NetworkPath(
        source="a",
        destination="b",
        packet_loss_pct=0.8,
    )
    assert degraded.health_status == "degraded"

    critical = NetworkPath(
        source="a",
        destination="b",
        packet_loss_pct=2.0,
    )
    assert critical.health_status == "critical"

    warning_latency = NetworkPath(
        source="a",
        destination="b",
        latency_ms=150.0,
        packet_loss_pct=0.0,
    )
    assert warning_latency.health_status == "warning"


def test_measurement_to_dict() -> None:
    """Test PerfSONARMeasurement serialization."""
    from datetime import datetime

    m = PerfSONARMeasurement(
        test_type=MeasurementType.THROUGHPUT,
        source="src",
        destination="dst",
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        value=9.5,
        unit="Gbps",
    )
    d = m.to_dict()
    assert d["test_type"] == "throughput"
    assert d["value"] == 9.5
    assert d["unit"] == "Gbps"


def test_nrp_nodes_defined() -> None:
    """Test that NRP nodes are properly defined."""
    assert len(NRP_NODES) >= 5
    assert "sdsc-prp.ucsd.edu" in NRP_NODES
