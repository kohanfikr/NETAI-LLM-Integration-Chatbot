"""Network telemetry request and response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class NetworkPathResponse(BaseModel):
    """Network path health information."""

    source: str
    destination: str
    throughput_gbps: float | None = None
    latency_ms: float | None = None
    packet_loss_pct: float | None = None
    jitter_ms: float | None = None
    retransmits_pct: float | None = None
    hop_count: int | None = None
    health_status: str
    last_updated: str | None = None


class NetworkSummaryResponse(BaseModel):
    """Overall network health summary."""

    timestamp: str
    total_paths: int
    healthy: int
    degraded: int
    warning: int
    critical: int
    paths: list[NetworkPathResponse]


class AnomalyResponse(BaseModel):
    """A detected network anomaly."""

    type: str
    severity: str
    source: str
    destination: str
    description: str
    detected_at: str
    current_value: float
    baseline_value: float
    threshold: float
    unit: str


class DiagnosticsRequest(BaseModel):
    """Request for path-specific diagnostics."""

    source: str = Field(
        ...,
        description="Source network endpoint",
        examples=["sdsc-prp.ucsd.edu"],
    )
    destination: str = Field(
        ...,
        description="Destination network endpoint",
        examples=["nrp-chi.uchicago.edu"],
    )


class TracerouteResponse(BaseModel):
    """Traceroute result."""

    source: str
    destination: str
    timestamp: str
    hop_count: int
    total_rtt_ms: float | None
    completed: bool
    hops: list[dict]
    problematic_hops: list[dict]


class PathDiagnosticsResponse(BaseModel):
    """Comprehensive diagnostics for a network path."""

    path: NetworkPathResponse
    traceroute: TracerouteResponse
    anomalies: list[AnomalyResponse]
    measurement_count: dict[str, int]
