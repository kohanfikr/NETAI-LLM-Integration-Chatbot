"""NETAI Chatbot — FastAPI Application Entry Point.

AI-Powered Kubernetes Chatbot for Network Diagnostics
on the National Research Platform (NRP).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from netai_chatbot import __version__
from netai_chatbot.api.middleware import setup_middleware
from netai_chatbot.api.routes import chat, health, telemetry
from netai_chatbot.config import get_settings
from netai_chatbot.context.manager import ContextManager
from netai_chatbot.diagnostics.perfsonar import PerfSONARClient
from netai_chatbot.diagnostics.telemetry import TelemetryProcessor
from netai_chatbot.diagnostics.traceroute import TracerouteAnalyzer
from netai_chatbot.llm.client import LLMClient, MockLLMClient
from netai_chatbot.llm.prompt_engine import PromptEngine
from netai_chatbot.utils import get_logger, setup_logging

STATIC_DIR = Path(__file__).parent.parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan — initialize and cleanup resources."""
    settings = get_settings()
    setup_logging(settings.app_log_level)
    logger = get_logger("netai_chatbot")

    logger.info(
        "starting",
        version=__version__,
        model=settings.llm_default_model.value,
        mock_data=settings.enable_mock_data,
    )

    # Initialize components
    perfsonar = PerfSONARClient(settings)
    traceroute_analyzer = TracerouteAnalyzer(enable_mock=settings.enable_mock_data)
    telemetry_processor = TelemetryProcessor(perfsonar, traceroute_analyzer)
    prompt_engine = PromptEngine()
    context_manager = ContextManager(prompt_engine, telemetry_processor, settings)

    # Use mock LLM client if API key is not configured
    if settings.llm_api_key == "mock-key-for-development" or settings.enable_mock_data:
        llm_client: LLMClient = MockLLMClient(settings)
        logger.info("using_mock_llm", reason="development mode")
    else:
        llm_client = LLMClient(settings)
        logger.info("using_nrp_llm", endpoint=settings.llm_api_base_url)

    # Wire up dependencies
    chat.init_chat_dependencies(llm_client, context_manager)
    telemetry.init_network_dependencies(telemetry_processor)

    logger.info("ready", host=settings.app_host, port=settings.app_port)

    yield

    # Cleanup
    await llm_client.close()
    await context_manager.close()
    logger.info("shutdown_complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="NETAI Chatbot",
        description=(
            "AI-Powered Kubernetes Chatbot for Network Diagnostics "
            "on the National Research Platform (NRP). "
            "Integrates with NRP's managed LLM service (Qwen3-VL, GLM-4.7, GPT-OSS) "
            "to provide intelligent network diagnostics assistance."
        ),
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Middleware
    setup_middleware(app)

    # Routes
    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(telemetry.router)

    # Static files (web UI)
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    return app


app = create_app()


def main() -> None:
    """Run the application with uvicorn."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "netai_chatbot.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
        log_level=settings.app_log_level,
    )


if __name__ == "__main__":
    main()
