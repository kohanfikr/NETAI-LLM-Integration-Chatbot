"""Tests for prompt engineering engine."""

from __future__ import annotations

from netai_chatbot.llm.prompt_engine import PromptEngine


def test_classify_anomaly_query(prompt_engine: PromptEngine) -> None:
    """Test query classification for anomaly-related queries."""
    assert (
        prompt_engine.classify_query("Is there an anomaly on the network?") == "anomaly_explanation"
    )
    assert prompt_engine.classify_query("I see a strange spike in latency") == "anomaly_explanation"
    assert prompt_engine.classify_query("Something unusual happened") == "anomaly_explanation"


def test_classify_remediation_query(prompt_engine: PromptEngine) -> None:
    """Test query classification for remediation queries."""
    assert prompt_engine.classify_query("How do I fix this issue?") == "remediation"
    assert prompt_engine.classify_query("What remediation steps should I take?") == "remediation"
    assert prompt_engine.classify_query("How to resolve packet loss?") == "remediation"


def test_classify_telemetry_query(prompt_engine: PromptEngine) -> None:
    """Test query classification for telemetry queries."""
    assert prompt_engine.classify_query("Show me the telemetry data") == "telemetry_analysis"
    assert prompt_engine.classify_query("What are the perfSONAR metrics?") == "telemetry_analysis"
    assert prompt_engine.classify_query("Latest measurement results") == "telemetry_analysis"


def test_classify_general_query(prompt_engine: PromptEngine) -> None:
    """Test query classification for general queries."""
    assert prompt_engine.classify_query("What is the throughput?") == "general_diagnostics"
    assert prompt_engine.classify_query("Hello") == "general_diagnostics"


def test_build_messages_basic(prompt_engine: PromptEngine) -> None:
    """Test building messages with just a user query."""
    messages = prompt_engine.build_messages("What is the throughput?")
    assert len(messages) == 2  # system + user
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "What is the throughput?"


def test_build_messages_with_history(prompt_engine: PromptEngine) -> None:
    """Test building messages with conversation history."""
    history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi! How can I help?"},
    ]
    messages = prompt_engine.build_messages("Check throughput", conversation_history=history)
    assert len(messages) == 4  # system + 2 history + user
    assert messages[1]["content"] == "Hello"
    assert messages[2]["content"] == "Hi! How can I help?"
    assert messages[3]["content"] == "Check throughput"


def test_build_messages_with_telemetry_context(prompt_engine: PromptEngine) -> None:
    """Test building messages with injected telemetry context."""
    context = "Throughput: 8.5 Gbps\nLatency: 25ms"
    messages = prompt_engine.build_messages(
        "What's happening?",
        telemetry_context=context,
    )
    assert "Throughput: 8.5 Gbps" in messages[0]["content"]
    assert "Latency: 25ms" in messages[0]["content"]


def test_list_templates(prompt_engine: PromptEngine) -> None:
    """Test listing available prompt templates."""
    templates = prompt_engine.list_templates()
    assert len(templates) >= 4
    names = {t["key"] for t in templates}
    assert "general_diagnostics" in names
    assert "telemetry_analysis" in names
    assert "anomaly_explanation" in names
    assert "remediation" in names


def test_get_system_prompt(prompt_engine: PromptEngine) -> None:
    """Test getting system prompts for different templates."""
    general = prompt_engine.get_system_prompt("general_diagnostics")
    assert "NETAI" in general
    assert "network diagnostics" in general.lower()

    anomaly = prompt_engine.get_system_prompt("anomaly_explanation")
    assert "anomaly" in anomaly.lower()

    # Fallback for unknown template
    fallback = prompt_engine.get_system_prompt("nonexistent")
    assert "NETAI" in fallback  # Falls back to default


def test_render_user_prompt(prompt_engine: PromptEngine) -> None:
    """Test rendering a user prompt template with variables."""
    rendered = prompt_engine.render_user_prompt(
        "anomaly_explanation",
        anomaly_type="Throughput Drop",
        severity="High",
        affected_path="UCSD → Chicago",
        metrics="Throughput: 3.2 Gbps (baseline: 8.5 Gbps)",
    )
    assert rendered is not None
    assert "Throughput Drop" in rendered
    assert "High" in rendered
    assert "UCSD → Chicago" in rendered
