"""Traceroute analysis for network path diagnostics.

Analyzes traceroute data to identify problematic hops, routing changes,
and correlate path-level issues with performance degradation.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class TracerouteHop:
    """A single hop in a traceroute path."""

    hop_number: int
    ip_address: str
    hostname: str | None = None
    rtt_ms: float | None = None
    asn: int | None = None
    location: str | None = None
    is_responding: bool = True

    def to_dict(self) -> dict:
        return {
            "hop": self.hop_number,
            "ip": self.ip_address,
            "hostname": self.hostname,
            "rtt_ms": self.rtt_ms,
            "asn": self.asn,
            "location": self.location,
            "responding": self.is_responding,
        }


@dataclass
class TracerouteResult:
    """Complete traceroute result between two endpoints."""

    source: str
    destination: str
    timestamp: datetime
    hops: list[TracerouteHop] = field(default_factory=list)
    completed: bool = True

    @property
    def hop_count(self) -> int:
        return len(self.hops)

    @property
    def total_rtt_ms(self) -> float | None:
        if self.hops and self.hops[-1].rtt_ms:
            return self.hops[-1].rtt_ms
        return None

    @property
    def problematic_hops(self) -> list[TracerouteHop]:
        """Identify hops with high latency increases or timeouts."""
        problems = []
        for i, hop in enumerate(self.hops):
            if not hop.is_responding:
                problems.append(hop)
            elif i > 0 and hop.rtt_ms and self.hops[i - 1].rtt_ms:
                delta = hop.rtt_ms - self.hops[i - 1].rtt_ms
                if delta > 20:  # >20ms increase between hops is suspicious
                    problems.append(hop)
        return problems

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "destination": self.destination,
            "timestamp": self.timestamp.isoformat(),
            "hop_count": self.hop_count,
            "total_rtt_ms": self.total_rtt_ms,
            "completed": self.completed,
            "problematic_hops": [h.to_dict() for h in self.problematic_hops],
            "hops": [h.to_dict() for h in self.hops],
        }

    def format_text(self) -> str:
        """Format traceroute as human-readable text for LLM context."""
        lines = [f"Traceroute from {self.source} to {self.destination}"]
        lines.append(f"Time: {self.timestamp.isoformat()}")
        lines.append("-" * 70)

        for hop in self.hops:
            if hop.is_responding:
                host = hop.hostname or hop.ip_address
                rtt = f"{hop.rtt_ms:.1f}ms" if hop.rtt_ms else "N/A"
                asn_str = f"  AS{hop.asn}" if hop.asn else ""
                loc = f"  [{hop.location}]" if hop.location else ""
                lines.append(f"  {hop.hop_number:>2}  {host:<40} {rtt:>10}{asn_str}{loc}")
            else:
                lines.append(f"  {hop.hop_number:>2}  * * *  (no response)")

        if self.problematic_hops:
            lines.append("")
            lines.append("⚠ Problematic hops detected:")
            for hop in self.problematic_hops:
                if not hop.is_responding:
                    lines.append(f"  - Hop {hop.hop_number}: No response (possible firewall)")
                else:
                    lines.append(
                        f"  - Hop {hop.hop_number} ({hop.hostname or hop.ip_address}): "
                        f"High latency ({hop.rtt_ms:.1f}ms)"
                    )

        return "\n".join(lines)


# Mock network topology for realistic traceroutes
MOCK_TOPOLOGY = {
    ("sdsc-prp.ucsd.edu", "nrp-chi.uchicago.edu"): [
        ("10.0.1.1", "gw-sdsc.ucsd.edu", "San Diego, CA", 64512),
        ("198.17.46.1", "cenic-la.cenic.org", "Los Angeles, CA", 2152),
        ("134.55.40.1", "esnet-snv.es.net", "Sunnyvale, CA", 293),
        ("134.55.50.5", "esnet-den.es.net", "Denver, CO", 293),
        ("134.55.60.1", "esnet-chi.es.net", "Chicago, IL", 293),
        ("192.170.232.1", "i2-chi.internet2.edu", "Chicago, IL", 11537),
        ("10.10.1.1", "gw-chi.uchicago.edu", "Chicago, IL", 160),
    ],
    ("nrp-chi.uchicago.edu", "nrp-sea.washington.edu"): [
        ("10.10.1.1", "gw-chi.uchicago.edu", "Chicago, IL", 160),
        ("192.170.232.5", "i2-chi.internet2.edu", "Chicago, IL", 11537),
        ("192.170.233.1", "i2-den.internet2.edu", "Denver, CO", 11537),
        ("192.170.234.1", "i2-sea.internet2.edu", "Seattle, WA", 11537),
        ("10.20.1.1", "gw-sea.washington.edu", "Seattle, WA", 73),
    ],
}


class TracerouteAnalyzer:
    """Analyzes traceroute data for network path diagnostics.

    Provides traceroute execution (mock in dev), path comparison,
    and hop-level analysis for identifying network issues.
    """

    def __init__(self, enable_mock: bool = True) -> None:
        self.enable_mock = enable_mock

    async def trace(self, source: str, destination: str) -> TracerouteResult:
        """Execute a traceroute between two endpoints."""
        if self.enable_mock:
            return self._mock_traceroute(source, destination)
        raise NotImplementedError("Production traceroute integration pending")

    async def compare_paths(
        self, source: str, destination: str, count: int = 2
    ) -> list[TracerouteResult]:
        """Run multiple traceroutes and compare paths for consistency."""
        results = []
        for _ in range(count):
            result = await self.trace(source, destination)
            results.append(result)
        return results

    def analyze_path_change(self, old: TracerouteResult, new: TracerouteResult) -> dict:
        """Detect routing changes between two traceroute results."""
        old_ips = {h.ip_address for h in old.hops}
        new_ips = {h.ip_address for h in new.hops}

        added = new_ips - old_ips
        removed = old_ips - new_ips

        return {
            "path_changed": bool(added or removed),
            "hops_added": list(added),
            "hops_removed": list(removed),
            "old_hop_count": old.hop_count,
            "new_hop_count": new.hop_count,
            "rtt_change_ms": ((new.total_rtt_ms or 0) - (old.total_rtt_ms or 0)),
        }

    def _mock_traceroute(self, source: str, destination: str) -> TracerouteResult:
        """Generate a realistic mock traceroute."""
        key = (source, destination)
        hop_data = MOCK_TOPOLOGY[key] if key in MOCK_TOPOLOGY else self._generate_random_path()

        hops = []
        cumulative_rtt = 0.0

        for i, (ip, hostname, location, asn) in enumerate(hop_data, 1):
            # Simulate realistic per-hop latency
            hop_latency = random.uniform(1.0, 15.0)
            # Occasionally a hop doesn't respond
            responding = random.random() > 0.05
            cumulative_rtt += hop_latency

            hops.append(
                TracerouteHop(
                    hop_number=i,
                    ip_address=ip,
                    hostname=hostname,
                    rtt_ms=round(cumulative_rtt, 2) if responding else None,
                    asn=asn,
                    location=location,
                    is_responding=responding,
                )
            )

        return TracerouteResult(
            source=source,
            destination=destination,
            timestamp=datetime.now(UTC),
            hops=hops,
            completed=True,
        )

    def _generate_random_path(self) -> list[tuple[str, str, str, int]]:
        """Generate a random but realistic-looking network path."""
        locations = [
            ("San Diego, CA", 64512),
            ("Los Angeles, CA", 2152),
            ("Denver, CO", 293),
            ("Kansas City, MO", 11537),
            ("Chicago, IL", 160),
        ]
        hop_count = random.randint(5, 12)
        path = []
        for i in range(hop_count):
            loc, asn = random.choice(locations)
            ip = f"{random.randint(10, 198)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
            hostname = f"router-{i + 1}.{loc.split(',')[0].lower().replace(' ', '')}.net"
            path.append((ip, hostname, loc, asn))
        return path
