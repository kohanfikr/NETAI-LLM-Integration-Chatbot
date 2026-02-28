"""Network telemetry and diagnostics API routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from netai_chatbot.api.models.telemetry import DiagnosticsRequest
from netai_chatbot.diagnostics.perfsonar import NRP_NODES
from netai_chatbot.diagnostics.telemetry import TelemetryProcessor
from netai_chatbot.utils import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/network", tags=["network"])

# Module-level state
_telemetry: TelemetryProcessor | None = None


def init_network_dependencies(telemetry: TelemetryProcessor) -> None:
    """Initialize network route dependencies."""
    global _telemetry
    _telemetry = telemetry


def _get_telemetry() -> TelemetryProcessor:
    if not _telemetry:
        raise HTTPException(status_code=503, detail="Telemetry not initialized")
    return _telemetry


@router.get("/summary")
async def network_summary() -> dict:
    """Get comprehensive network health summary across all monitored paths."""
    telemetry = _get_telemetry()
    return await telemetry.get_network_summary()


@router.post("/diagnostics")
async def path_diagnostics(request: DiagnosticsRequest) -> dict:
    """Get detailed diagnostics for a specific network path.

    Includes throughput, latency, traceroute analysis, and anomaly detection.
    """
    telemetry = _get_telemetry()
    try:
        return await telemetry.get_path_diagnostics(request.source, request.destination)
    except Exception as e:
        logger.error("diagnostics_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Diagnostics error: {e!s}") from e


@router.post("/traceroute")
async def run_traceroute(request: DiagnosticsRequest) -> dict:
    """Execute a traceroute between two network endpoints."""
    telemetry = _get_telemetry()
    result = await telemetry.traceroute.trace(request.source, request.destination)
    return result.to_dict()


@router.get("/nodes")
async def list_nodes() -> dict:
    """List available NRP network nodes."""
    return {
        "nodes": NRP_NODES,
        "count": len(NRP_NODES),
    }


@router.get("/paths/{source}/{destination}")
async def get_path_health(source: str, destination: str) -> dict:
    """Get health metrics for a specific network path."""
    telemetry = _get_telemetry()
    path = await telemetry.perfsonar.get_path_health(source, destination)
    return path.to_dict()
