"""Shared test fixtures for NETAI Chatbot test suite."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from netai_chatbot.api.routes import chat, telemetry
from netai_chatbot.config import Settings
from netai_chatbot.context.manager import ContextManager
from netai_chatbot.diagnostics.anomaly import AnomalyDetector
from netai_chatbot.diagnostics.perfsonar import PerfSONARClient
from netai_chatbot.diagnostics.telemetry import TelemetryProcessor
from netai_chatbot.diagnostics.traceroute import TracerouteAnalyzer
from netai_chatbot.llm.client import MockLLMClient
from netai_chatbot.llm.prompt_engine import PromptEngine
from netai_chatbot.main import create_app


@pytest.fixture
def settings() -> Settings:
    """Test settings with mock data enabled."""
    return Settings(
        llm_api_key="test-key",
        enable_mock_data=True,
        app_debug=True,
    )


@pytest.fixture
def mock_llm_client(settings: Settings) -> MockLLMClient:
    """Mock LLM client for testing."""
    return MockLLMClient(settings)


@pytest.fixture
def prompt_engine() -> PromptEngine:
    """Prompt engine instance."""
    return PromptEngine()


@pytest.fixture
def perfsonar_client(settings: Settings) -> PerfSONARClient:
    """perfSONAR client with mock data."""
    return PerfSONARClient(settings)


@pytest.fixture
def traceroute_analyzer() -> TracerouteAnalyzer:
    """Traceroute analyzer with mock data."""
    return TracerouteAnalyzer(enable_mock=True)


@pytest.fixture
def anomaly_detector() -> AnomalyDetector:
    """Anomaly detector instance."""
    return AnomalyDetector()


@pytest.fixture
def telemetry_processor(
    perfsonar_client: PerfSONARClient,
    traceroute_analyzer: TracerouteAnalyzer,
    anomaly_detector: AnomalyDetector,
) -> TelemetryProcessor:
    """Telemetry processor with mock dependencies."""
    return TelemetryProcessor(perfsonar_client, traceroute_analyzer, anomaly_detector)


@pytest.fixture
def context_manager(
    prompt_engine: PromptEngine,
    telemetry_processor: TelemetryProcessor,
    settings: Settings,
) -> ContextManager:
    """Context manager with mock dependencies."""
    return ContextManager(prompt_engine, telemetry_processor, settings)


@pytest.fixture
async def async_client(settings: Settings) -> AsyncClient:
    """Async HTTP test client with dependencies manually wired."""
    app = create_app()

    # Manually initialize dependencies (lifespan doesn't run in test transport)
    perfsonar = PerfSONARClient(settings)
    traceroute_analyzer = TracerouteAnalyzer(enable_mock=True)
    telemetry_processor = TelemetryProcessor(perfsonar, traceroute_analyzer)
    prompt_engine = PromptEngine()
    context_manager = ContextManager(prompt_engine, telemetry_processor, settings)
    llm_client = MockLLMClient(settings)

    chat.init_chat_dependencies(llm_client, context_manager)
    telemetry.init_network_dependencies(telemetry_processor)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    await llm_client.close()
    await context_manager.close()
