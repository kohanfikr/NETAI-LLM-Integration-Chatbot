"""Tests for traceroute analysis."""

from __future__ import annotations

import pytest

from netai_chatbot.diagnostics.traceroute import TracerouteAnalyzer, TracerouteResult


@pytest.mark.asyncio
async def test_trace(traceroute_analyzer: TracerouteAnalyzer) -> None:
    """Test executing a traceroute."""
    result = await traceroute_analyzer.trace("sdsc-prp.ucsd.edu", "nrp-chi.uchicago.edu")
    assert isinstance(result, TracerouteResult)
    assert result.source == "sdsc-prp.ucsd.edu"
    assert result.destination == "nrp-chi.uchicago.edu"
    assert result.hop_count > 0
    assert result.completed


@pytest.mark.asyncio
async def test_trace_hops_have_data(traceroute_analyzer: TracerouteAnalyzer) -> None:
    """Test that traceroute hops contain expected data."""
    result = await traceroute_analyzer.trace("sdsc-prp.ucsd.edu", "nrp-chi.uchicago.edu")
    for hop in result.hops:
        assert hop.hop_number > 0
        assert hop.ip_address
        if hop.is_responding:
            assert hop.rtt_ms is not None or not hop.is_responding


@pytest.mark.asyncio
async def test_compare_paths(traceroute_analyzer: TracerouteAnalyzer) -> None:
    """Test comparing multiple traceroute runs."""
    results = await traceroute_analyzer.compare_paths(
        "sdsc-prp.ucsd.edu", "nrp-chi.uchicago.edu", count=2
    )
    assert len(results) == 2
    assert all(isinstance(r, TracerouteResult) for r in results)


@pytest.mark.asyncio
async def test_analyze_path_change(traceroute_analyzer: TracerouteAnalyzer) -> None:
    """Test path change analysis between two traceroutes."""
    results = await traceroute_analyzer.compare_paths(
        "sdsc-prp.ucsd.edu", "nrp-chi.uchicago.edu", count=2
    )
    analysis = traceroute_analyzer.analyze_path_change(results[0], results[1])
    assert "path_changed" in analysis
    assert "old_hop_count" in analysis
    assert "new_hop_count" in analysis
    assert "rtt_change_ms" in analysis


@pytest.mark.asyncio
async def test_traceroute_to_dict(traceroute_analyzer: TracerouteAnalyzer) -> None:
    """Test traceroute serialization."""
    result = await traceroute_analyzer.trace("sdsc-prp.ucsd.edu", "nrp-chi.uchicago.edu")
    d = result.to_dict()
    assert d["source"] == "sdsc-prp.ucsd.edu"
    assert "hops" in d
    assert "hop_count" in d
    assert isinstance(d["hops"], list)


@pytest.mark.asyncio
async def test_traceroute_format_text(traceroute_analyzer: TracerouteAnalyzer) -> None:
    """Test traceroute text formatting for LLM context."""
    result = await traceroute_analyzer.trace("sdsc-prp.ucsd.edu", "nrp-chi.uchicago.edu")
    text = result.format_text()
    assert "sdsc-prp.ucsd.edu" in text
    assert "nrp-chi.uchicago.edu" in text
