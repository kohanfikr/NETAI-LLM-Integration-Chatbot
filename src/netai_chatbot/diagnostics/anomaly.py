"""Basic anomaly detection for network metrics.

Provides threshold-based and statistical anomaly detection on
perfSONAR measurements and network telemetry data.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from netai_chatbot.diagnostics.perfsonar import PerfSONARMeasurement


class AnomalySeverity(StrEnum):
    """Anomaly severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AnomalyType(StrEnum):
    """Types of network anomalies."""

    THROUGHPUT_DROP = "throughput_drop"
    LATENCY_SPIKE = "latency_spike"
    PACKET_LOSS = "packet_loss"
    JITTER_INCREASE = "jitter_increase"
    PATH_CHANGE = "path_change"
    LINK_FLAP = "link_flap"


@dataclass
class Anomaly:
    """A detected network anomaly."""

    anomaly_type: AnomalyType
    severity: AnomalySeverity
    source: str
    destination: str
    description: str
    detected_at: datetime
    current_value: float
    baseline_value: float
    threshold: float
    unit: str

    def to_dict(self) -> dict:
        return {
            "type": self.anomaly_type.value,
            "severity": self.severity.value,
            "source": self.source,
            "destination": self.destination,
            "description": self.description,
            "detected_at": self.detected_at.isoformat(),
            "current_value": self.current_value,
            "baseline_value": self.baseline_value,
            "threshold": self.threshold,
            "unit": self.unit,
        }

    def format_for_llm(self) -> str:
        """Format anomaly for injection into LLM context."""
        return (
            f"**{self.anomaly_type.value.replace('_', ' ').title()}** "
            f"[{self.severity.value.upper()}]\n"
            f"Path: {self.source} → {self.destination}\n"
            f"Current: {self.current_value} {self.unit} "
            f"(baseline: {self.baseline_value} {self.unit}, "
            f"threshold: {self.threshold} {self.unit})\n"
            f"Detected: {self.detected_at.isoformat()}\n"
            f"Description: {self.description}"
        )


# Default thresholds for NRP network
DEFAULT_THRESHOLDS = {
    "throughput_drop_pct": 20,  # Alert if throughput drops >20% from baseline
    "latency_spike_pct": 50,  # Alert if latency increases >50% from baseline
    "packet_loss_pct": 0.5,  # Alert if packet loss >0.5%
    "jitter_ms": 10,  # Alert if jitter >10ms
}


class AnomalyDetector:
    """Detects anomalies in network measurements using threshold and statistical methods.

    Uses a combination of:
    - Static threshold-based detection
    - Z-score based statistical detection
    - Moving average deviation detection
    """

    def __init__(self, thresholds: dict[str, float] | None = None) -> None:
        self.thresholds = thresholds or DEFAULT_THRESHOLDS

    def detect_throughput_anomalies(
        self,
        measurements: list[PerfSONARMeasurement],
        source: str = "",
        destination: str = "",
    ) -> list[Anomaly]:
        """Detect throughput anomalies using statistical analysis."""
        if len(measurements) < 5:
            return []

        values = [m.value for m in measurements]
        mean_val = statistics.mean(values)
        stdev_val = statistics.stdev(values) if len(values) > 1 else 0

        anomalies = []
        threshold_pct = self.thresholds["throughput_drop_pct"]

        for m in measurements[-10:]:  # Check recent measurements
            drop_pct = ((mean_val - m.value) / mean_val) * 100 if mean_val > 0 else 0
            z_score = (m.value - mean_val) / stdev_val if stdev_val > 0 else 0

            if drop_pct > threshold_pct or z_score < -2:
                severity = self._classify_severity(drop_pct, [20, 40, 60])
                anomalies.append(
                    Anomaly(
                        anomaly_type=AnomalyType.THROUGHPUT_DROP,
                        severity=severity,
                        source=source or m.source,
                        destination=destination or m.destination,
                        description=(
                            f"Throughput dropped {drop_pct:.1f}% below baseline "
                            f"({m.value:.2f} Gbps vs {mean_val:.2f} Gbps baseline). "
                            f"Z-score: {z_score:.2f}"
                        ),
                        detected_at=m.timestamp,
                        current_value=round(m.value, 2),
                        baseline_value=round(mean_val, 2),
                        threshold=round(mean_val * (1 - threshold_pct / 100), 2),
                        unit="Gbps",
                    )
                )

        return anomalies

    def detect_latency_anomalies(
        self,
        measurements: list[PerfSONARMeasurement],
        source: str = "",
        destination: str = "",
    ) -> list[Anomaly]:
        """Detect latency anomalies using statistical analysis."""
        if len(measurements) < 5:
            return []

        values = [m.value for m in measurements]
        mean_val = statistics.mean(values)
        stdev_val = statistics.stdev(values) if len(values) > 1 else 0

        anomalies = []
        threshold_pct = self.thresholds["latency_spike_pct"]

        for m in measurements[-10:]:
            spike_pct = ((m.value - mean_val) / mean_val) * 100 if mean_val > 0 else 0
            z_score = (m.value - mean_val) / stdev_val if stdev_val > 0 else 0

            if spike_pct > threshold_pct or z_score > 2:
                severity = self._classify_severity(spike_pct, [50, 100, 200])
                anomalies.append(
                    Anomaly(
                        anomaly_type=AnomalyType.LATENCY_SPIKE,
                        severity=severity,
                        source=source or m.source,
                        destination=destination or m.destination,
                        description=(
                            f"Latency spiked {spike_pct:.1f}% above baseline "
                            f"({m.value:.2f}ms vs {mean_val:.2f}ms baseline). "
                            f"Z-score: {z_score:.2f}"
                        ),
                        detected_at=m.timestamp,
                        current_value=round(m.value, 2),
                        baseline_value=round(mean_val, 2),
                        threshold=round(mean_val * (1 + threshold_pct / 100), 2),
                        unit="ms",
                    )
                )

        return anomalies

    def detect_all(
        self,
        throughput_data: list[PerfSONARMeasurement],
        latency_data: list[PerfSONARMeasurement],
        source: str = "",
        destination: str = "",
    ) -> list[Anomaly]:
        """Run all anomaly detection algorithms on available data."""
        anomalies = []
        anomalies.extend(self.detect_throughput_anomalies(throughput_data, source, destination))
        anomalies.extend(self.detect_latency_anomalies(latency_data, source, destination))
        # Sort by severity (critical first)
        severity_order = {
            AnomalySeverity.CRITICAL: 0,
            AnomalySeverity.HIGH: 1,
            AnomalySeverity.MEDIUM: 2,
            AnomalySeverity.LOW: 3,
        }
        anomalies.sort(key=lambda a: severity_order[a.severity])
        return anomalies

    @staticmethod
    def _classify_severity(deviation_pct: float, thresholds: list[float]) -> AnomalySeverity:
        """Classify anomaly severity based on deviation percentage."""
        if deviation_pct >= thresholds[2]:
            return AnomalySeverity.CRITICAL
        if deviation_pct >= thresholds[1]:
            return AnomalySeverity.HIGH
        if deviation_pct >= thresholds[0]:
            return AnomalySeverity.MEDIUM
        return AnomalySeverity.LOW
