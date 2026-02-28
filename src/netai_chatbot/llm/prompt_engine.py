"""Prompt engineering strategies for network diagnostics domain."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PromptTemplate:
    """A reusable prompt template with variable interpolation."""

    name: str
    system_prompt: str
    user_template: str | None = None
    description: str = ""


# ─── System Prompts ───────────────────────────────────────────────────

NETWORK_DIAGNOSTICS_SYSTEM_PROMPT = """\
You are NETAI, an expert AI assistant for network diagnostics and operations on the \
National Research Platform (NRP). You help network operators understand complex network \
behaviors, diagnose anomalies, and provide actionable remediation strategies.

Your expertise includes:
- perfSONAR measurement analysis (throughput, latency, packet loss, traceroute)
- Network path analysis and hop-by-hop diagnostics
- BGP routing and traffic engineering
- Optical network troubleshooting
- Kubernetes networking and service mesh diagnostics

When analyzing network issues:
1. Start with a clear summary of what you observe
2. Identify likely root causes based on the data
3. Correlate multiple data sources when available
4. Provide specific, actionable remediation steps
5. Rate the severity (Low/Medium/High/Critical)

Always format your responses with clear Markdown headers and bullet points. \
When discussing metrics, include specific values and comparisons to baselines. \
If you're uncertain about a diagnosis, say so and suggest additional data collection steps."""

TELEMETRY_ANALYSIS_SYSTEM_PROMPT = """\
You are analyzing network telemetry data from the National Research Platform. \
The data comes from perfSONAR measurements and includes throughput tests, \
latency measurements, packet loss statistics, and traceroute results.

When presented with telemetry data:
- Compare current values against historical baselines
- Flag any metrics that exceed standard thresholds
- Identify trends and correlations between metrics
- Suggest whether the observed behavior is normal or anomalous

Standard thresholds for NRP network:
- Throughput: Alert if <80% of baseline capacity
- Latency (RTT): Alert if >150% of baseline
- Packet loss: Alert if >0.5%
- Jitter: Alert if >10ms for research traffic
- Retransmits: Alert if >1% of total packets"""

ANOMALY_EXPLANATION_SYSTEM_PROMPT = """\
You are explaining a detected network anomaly to a network operator. \
Provide a clear, technically accurate explanation that includes:

1. **What happened**: Describe the anomaly in plain language
2. **Impact**: What services or paths are affected
3. **Likely cause**: Most probable root cause based on the data
4. **Evidence**: Specific metrics and observations supporting the diagnosis
5. **Remediation**: Step-by-step actions to resolve the issue
6. **Prevention**: How to prevent recurrence

Be specific with metric values, timestamps, and affected network elements. \
Use network engineering terminology appropriately."""

REMEDIATION_SYSTEM_PROMPT = """\
You are providing network remediation strategies for the National Research Platform. \
For each issue, provide:

1. **Immediate actions** (within 15 minutes): Emergency mitigation steps
2. **Short-term fixes** (within 24 hours): Proper resolution steps
3. **Long-term improvements** (within 1 week+): Preventive measures

Include specific CLI commands for network equipment when applicable (Juniper/Cisco). \
Estimate the impact of each action on network traffic. \
Prioritize actions that minimize disruption to research workflows."""


# ─── Prompt Templates ─────────────────────────────────────────────────

TEMPLATES: dict[str, PromptTemplate] = {
    "general_diagnostics": PromptTemplate(
        name="General Network Diagnostics",
        system_prompt=NETWORK_DIAGNOSTICS_SYSTEM_PROMPT,
        description="General-purpose network diagnostics assistant",
    ),
    "telemetry_analysis": PromptTemplate(
        name="Telemetry Analysis",
        system_prompt=TELEMETRY_ANALYSIS_SYSTEM_PROMPT,
        user_template=(
            "Analyze the following network telemetry data:\n\n"
            "{telemetry_data}\n\n"
            "Provide a summary of the network health and flag any concerns."
        ),
        description="Analyze raw telemetry data and provide health assessment",
    ),
    "anomaly_explanation": PromptTemplate(
        name="Anomaly Explanation",
        system_prompt=ANOMALY_EXPLANATION_SYSTEM_PROMPT,
        user_template=(
            "An anomaly has been detected:\n\n"
            "**Type**: {anomaly_type}\n"
            "**Severity**: {severity}\n"
            "**Affected Path**: {affected_path}\n"
            "**Metrics**:\n{metrics}\n\n"
            "Please explain this anomaly and recommend remediation steps."
        ),
        description="Explain a detected network anomaly with remediation",
    ),
    "remediation": PromptTemplate(
        name="Remediation Strategy",
        system_prompt=REMEDIATION_SYSTEM_PROMPT,
        user_template=(
            "Provide remediation strategies for the following network issue:\n\n"
            "**Issue**: {issue_description}\n"
            "**Affected Systems**: {affected_systems}\n"
            "**Current Impact**: {impact}\n"
        ),
        description="Generate remediation strategies for network issues",
    ),
}


class PromptEngine:
    """Prompt engineering engine for network diagnostics queries.

    Manages system prompts, context injection, and template rendering
    to produce optimal prompts for the NRP LLM service.
    """

    def __init__(self) -> None:
        self.templates = TEMPLATES

    def get_system_prompt(self, template_name: str = "general_diagnostics") -> str:
        """Get the system prompt for a specific diagnostics context."""
        template = self.templates.get(template_name)
        if not template:
            return NETWORK_DIAGNOSTICS_SYSTEM_PROMPT
        return template.system_prompt

    def render_user_prompt(self, template_name: str, **kwargs: str) -> str | None:
        """Render a user prompt template with provided variables."""
        template = self.templates.get(template_name)
        if not template or not template.user_template:
            return None
        return template.user_template.format(**kwargs)

    def build_messages(
        self,
        user_message: str,
        conversation_history: list[dict[str, str]] | None = None,
        template_name: str = "general_diagnostics",
        telemetry_context: str | None = None,
    ) -> list[dict[str, str]]:
        """Build the full message list for an LLM API call.

        Args:
            user_message: The user's current query.
            conversation_history: Previous messages in the conversation.
            template_name: Which prompt template to use.
            telemetry_context: Optional real-time network telemetry to inject.

        Returns:
            List of message dicts ready for the LLM API.
        """
        messages: list[dict[str, str]] = []

        # System prompt
        system_prompt = self.get_system_prompt(template_name)
        if telemetry_context:
            system_prompt += f"\n\n---\n**Current Network Telemetry Context**:\n{telemetry_context}"
        messages.append({"role": "system", "content": system_prompt})

        # Conversation history
        if conversation_history:
            messages.extend(conversation_history)

        # Current user message
        messages.append({"role": "user", "content": user_message})

        return messages

    def classify_query(self, user_message: str) -> str:
        """Classify a user query to select the best prompt template.

        Returns the template name that best matches the query intent.
        """
        message_lower = user_message.lower()

        if any(kw in message_lower for kw in ["anomaly", "unusual", "strange", "weird", "spike"]):
            return "anomaly_explanation"
        if any(kw in message_lower for kw in ["fix", "remediat", "resolve", "repair", "action"]):
            return "remediation"
        if any(
            kw in message_lower
            for kw in ["telemetry", "metric", "measurement", "perfsonar", "data"]
        ):
            return "telemetry_analysis"
        return "general_diagnostics"

    def list_templates(self) -> list[dict[str, str]]:
        """List all available prompt templates."""
        return [
            {"name": t.name, "key": key, "description": t.description}
            for key, t in self.templates.items()
        ]
