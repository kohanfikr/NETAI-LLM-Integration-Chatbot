"""Network telemetry processing and formatting for LLM context injection."""

from __future__ import annotations

from datetime import UTC, datetime

from netai_chatbot.diagnostics.anomaly import Anomaly, AnomalyDetector
from netai_chatbot.diagnostics.perfsonar import PerfSONARClient
from netai_chatbot.diagnostics.traceroute import TracerouteAnalyzer, TracerouteResult
from netai_chatbot.utils import get_logger

logger = get_logger(__name__)


class TelemetryProcessor:
    """Processes and formats network telemetry data for LLM context.

    Aggregates data from perfSONAR, traceroute, and anomaly detection
    into structured context that can be injected into LLM prompts.
    """

    def __init__(
        self,
        perfsonar: PerfSONARClient | None = None,
        traceroute: TracerouteAnalyzer | None = None,
        anomaly_detector: AnomalyDetector | None = None,
    ) -> None:
        self.perfsonar = perfsonar or PerfSONARClient()
        self.traceroute = traceroute or TracerouteAnalyzer()
        self.anomaly_detector = anomaly_detector or AnomalyDetector()

    async def get_network_summary(self) -> dict:
        """Get a comprehensive network health summary."""
        paths = await self.perfsonar.get_network_paths()

        healthy = sum(1 for p in paths if p.health_status == "healthy")
        degraded = sum(1 for p in paths if p.health_status == "degraded")
        warning = sum(1 for p in paths if p.health_status == "warning")
        critical = sum(1 for p in paths if p.health_status == "critical")

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "total_paths": len(paths),
            "healthy": healthy,
            "degraded": degraded,
            "warning": warning,
            "critical": critical,
            "paths": [p.to_dict() for p in paths],
        }

    async def get_path_diagnostics(self, source: str, destination: str) -> dict:
        """Get comprehensive diagnostics for a specific network path."""
        # Gather data in parallel conceptually
        path_health = await self.perfsonar.get_path_health(source, destination)
        traceroute_result = await self.traceroute.trace(source, destination)
        throughput_data = await self.perfsonar.get_throughput(source, destination, 24)
        latency_data = await self.perfsonar.get_latency(source, destination, 24)

        anomalies = self.anomaly_detector.detect_all(
            throughput_data, latency_data, source, destination
        )

        return {
            "path": path_health.to_dict(),
            "traceroute": traceroute_result.to_dict(),
            "anomalies": [a.to_dict() for a in anomalies],
            "measurement_count": {
                "throughput": len(throughput_data),
                "latency": len(latency_data),
            },
        }

    async def format_telemetry_context(
        self,
        source: str | None = None,
        destination: str | None = None,
    ) -> str:
        """Format current network telemetry as text for LLM context injection.

        This produces a concise summary that gets appended to the system prompt
        so the LLM has real-time awareness of network conditions.
        """
        lines: list[str] = []

        if source and destination:
            path = await self.perfsonar.get_path_health(source, destination)
            lines.append(f"**Path**: {source} → {destination}")
            lines.append(f"**Status**: {path.health_status.upper()}")
            lines.append(f"**Throughput**: {path.throughput_gbps} Gbps")
            lines.append(f"**Latency**: {path.latency_ms}ms")
            lines.append(f"**Packet Loss**: {path.packet_loss_pct}%")
            lines.append(f"**Jitter**: {path.jitter_ms}ms")

            # Check for anomalies
            throughput = await self.perfsonar.get_throughput(source, destination, 6)
            latency = await self.perfsonar.get_latency(source, destination, 6)
            anomalies = self.anomaly_detector.detect_all(throughput, latency, source, destination)
            if anomalies:
                lines.append(f"\n**Active Anomalies** ({len(anomalies)}):")
                for a in anomalies[:3]:
                    lines.append(f"- {a.format_for_llm()}")
        else:
            summary = await self.get_network_summary()
            lines.append(f"**Network Overview** ({summary['total_paths']} monitored paths)")
            lines.append(f"- Healthy: {summary['healthy']}")
            lines.append(f"- Warning: {summary['warning']}")
            lines.append(f"- Degraded: {summary['degraded']}")
            lines.append(f"- Critical: {summary['critical']}")

        return "\n".join(lines)

    def format_anomalies_context(self, anomalies: list[Anomaly]) -> str:
        """Format a list of anomalies for LLM context."""
        if not anomalies:
            return "No active anomalies detected."
        parts = [f"**{len(anomalies)} Active Anomalies:**\n"]
        for i, a in enumerate(anomalies, 1):
            parts.append(f"{i}. {a.format_for_llm()}\n")
        return "\n".join(parts)

    def format_traceroute_context(self, trace: TracerouteResult) -> str:
        """Format a traceroute result for LLM context."""
        return trace.format_text()

    async def close(self) -> None:
        await self.perfsonar.close()
