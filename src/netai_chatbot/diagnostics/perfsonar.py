"""perfSONAR data integration for network measurement analysis.

Provides access to network throughput, latency, and packet loss measurements
from perfSONAR nodes deployed across the National Research Platform.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum

import httpx

from netai_chatbot.config import Settings, get_settings
from netai_chatbot.utils import get_logger

logger = get_logger(__name__)


class MeasurementType(StrEnum):
    """perfSONAR measurement test types."""

    THROUGHPUT = "throughput"
    LATENCY = "latency"
    TRACE = "trace"
    RTT = "rtt"


@dataclass
class PerfSONARMeasurement:
    """A single perfSONAR measurement result."""

    test_type: MeasurementType
    source: str
    destination: str
    timestamp: datetime
    value: float
    unit: str
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "test_type": self.test_type.value,
            "source": self.source,
            "destination": self.destination,
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "unit": self.unit,
            "metadata": self.metadata,
        }


@dataclass
class NetworkPath:
    """A network path between two endpoints with associated measurements."""

    source: str
    destination: str
    throughput_gbps: float | None = None
    latency_ms: float | None = None
    packet_loss_pct: float | None = None
    jitter_ms: float | None = None
    retransmits_pct: float | None = None
    hop_count: int | None = None
    last_updated: datetime | None = None

    @property
    def health_status(self) -> str:
        """Compute network path health based on metrics."""
        if self.packet_loss_pct and self.packet_loss_pct > 1.0:
            return "critical"
        if self.packet_loss_pct and self.packet_loss_pct > 0.5:
            return "degraded"
        if self.latency_ms and self.latency_ms > 100:
            return "warning"
        if self.throughput_gbps and self.throughput_gbps < 1.0:
            return "warning"
        return "healthy"

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "destination": self.destination,
            "throughput_gbps": self.throughput_gbps,
            "latency_ms": self.latency_ms,
            "packet_loss_pct": self.packet_loss_pct,
            "jitter_ms": self.jitter_ms,
            "retransmits_pct": self.retransmits_pct,
            "hop_count": self.hop_count,
            "health_status": self.health_status,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }


# NRP network nodes for realistic mock data
NRP_NODES = [
    "sdsc-prp.ucsd.edu",
    "fiona-10g.ucsd.edu",
    "stashcache.t2.ucsd.edu",
    "k8s-gen4-01.sdsc.edu",
    "nrp-chi.uchicago.edu",
    "nrp-den.colorado.edu",
    "nrp-sea.washington.edu",
    "nrp-nyc.columbia.edu",
    "nrp-atl.gatech.edu",
    "nrp-aus.utexas.edu",
]


class PerfSONARClient:
    """Client for querying perfSONAR measurement data.

    In production, this connects to perfSONAR MA (Measurement Archive) APIs.
    In development, returns realistic mock data based on NRP topology.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._client: httpx.AsyncClient | None = None
        if not self.settings.enable_mock_data:
            self._client = httpx.AsyncClient(
                base_url=self.settings.perfsonar_url,
                timeout=30.0,
            )

    async def get_throughput(
        self, source: str, destination: str, time_range_hours: int = 24
    ) -> list[PerfSONARMeasurement]:
        """Get throughput measurements between two endpoints."""
        if self.settings.enable_mock_data:
            return self._mock_throughput(source, destination, time_range_hours)
        return await self._fetch_measurements(
            MeasurementType.THROUGHPUT, source, destination, time_range_hours
        )

    async def get_latency(
        self, source: str, destination: str, time_range_hours: int = 24
    ) -> list[PerfSONARMeasurement]:
        """Get latency (RTT) measurements between two endpoints."""
        if self.settings.enable_mock_data:
            return self._mock_latency(source, destination, time_range_hours)
        return await self._fetch_measurements(
            MeasurementType.LATENCY, source, destination, time_range_hours
        )

    async def get_network_paths(self) -> list[NetworkPath]:
        """Get all monitored network paths with current metrics."""
        if self.settings.enable_mock_data:
            return self._mock_network_paths()

        # Production: query perfSONAR MA
        paths = []
        # Implementation would query perfSONAR REST API
        return paths

    async def get_path_health(self, source: str, destination: str) -> NetworkPath:
        """Get health summary for a specific network path."""
        if self.settings.enable_mock_data:
            return self._mock_path_health(source, destination)

        # Production: aggregate measurements for this path
        raise NotImplementedError("Production perfSONAR integration pending")

    async def _fetch_measurements(
        self,
        test_type: MeasurementType,
        source: str,
        destination: str,
        time_range_hours: int,
    ) -> list[PerfSONARMeasurement]:
        """Fetch measurements from perfSONAR MA REST API."""
        if not self._client:
            return []

        params = {
            "source": source,
            "destination": destination,
            "event-type": test_type.value,
            "time-range": time_range_hours * 3600,
        }
        response = await self._client.get("/esmond/perfsonar/archive/", params=params)
        response.raise_for_status()
        # Parse and return measurements
        return []

    # ─── Mock Data Generators ─────────────────────────────────────────

    def _mock_throughput(
        self, source: str, destination: str, hours: int
    ) -> list[PerfSONARMeasurement]:
        """Generate realistic mock throughput data."""
        now = datetime.now(UTC)
        measurements = []
        baseline_gbps = random.uniform(5.0, 10.0)

        for i in range(hours * 4):  # 15-min intervals
            ts = now - timedelta(minutes=15 * i)
            # Simulate some variation with occasional dips
            variation = random.gauss(0, 0.3)
            dip = -2.0 if random.random() < 0.05 else 0  # 5% chance of throughput dip
            value = max(0.5, baseline_gbps + variation + dip)

            measurements.append(
                PerfSONARMeasurement(
                    test_type=MeasurementType.THROUGHPUT,
                    source=source,
                    destination=destination,
                    timestamp=ts,
                    value=round(value, 2),
                    unit="Gbps",
                    metadata={"tool": "iperf3", "duration": 20},
                )
            )
        return measurements

    def _mock_latency(
        self, source: str, destination: str, hours: int
    ) -> list[PerfSONARMeasurement]:
        """Generate realistic mock latency data."""
        now = datetime.now(UTC)
        measurements = []
        baseline_ms = random.uniform(10.0, 50.0)

        for i in range(hours * 60):  # 1-min intervals
            ts = now - timedelta(minutes=i)
            variation = random.gauss(0, 2.0)
            spike = 30.0 if random.random() < 0.02 else 0  # 2% chance of latency spike
            value = max(1.0, baseline_ms + variation + spike)

            measurements.append(
                PerfSONARMeasurement(
                    test_type=MeasurementType.LATENCY,
                    source=source,
                    destination=destination,
                    timestamp=ts,
                    value=round(value, 2),
                    unit="ms",
                    metadata={"tool": "owping", "sample_size": 100},
                )
            )
        return measurements

    def _mock_network_paths(self) -> list[NetworkPath]:
        """Generate mock network paths across NRP topology."""
        paths = []
        now = datetime.now(UTC)

        for i in range(0, len(NRP_NODES) - 1, 2):
            src, dst = NRP_NODES[i], NRP_NODES[i + 1]
            loss = random.choices(
                [0.0, random.uniform(0.01, 0.3), random.uniform(0.5, 2.0)],
                weights=[0.7, 0.2, 0.1],
            )[0]

            paths.append(
                NetworkPath(
                    source=src,
                    destination=dst,
                    throughput_gbps=round(random.uniform(3.0, 10.0), 2),
                    latency_ms=round(random.uniform(5.0, 80.0), 2),
                    packet_loss_pct=round(loss, 3),
                    jitter_ms=round(random.uniform(0.5, 8.0), 2),
                    retransmits_pct=round(random.uniform(0.0, 0.5), 3),
                    hop_count=random.randint(4, 15),
                    last_updated=now - timedelta(minutes=random.randint(0, 30)),
                )
            )
        return paths

    def _mock_path_health(self, source: str, destination: str) -> NetworkPath:
        """Generate mock health data for a specific path."""
        now = datetime.now(UTC)
        loss = random.choices(
            [0.0, random.uniform(0.01, 0.3), random.uniform(0.5, 2.0)],
            weights=[0.7, 0.2, 0.1],
        )[0]

        return NetworkPath(
            source=source,
            destination=destination,
            throughput_gbps=round(random.uniform(3.0, 10.0), 2),
            latency_ms=round(random.uniform(5.0, 80.0), 2),
            packet_loss_pct=round(loss, 3),
            jitter_ms=round(random.uniform(0.5, 8.0), 2),
            retransmits_pct=round(random.uniform(0.0, 0.5), 3),
            hop_count=random.randint(4, 15),
            last_updated=now,
        )

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
