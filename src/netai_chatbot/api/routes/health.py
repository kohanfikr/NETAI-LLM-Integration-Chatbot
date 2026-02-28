"""Health check endpoints for Kubernetes readiness/liveness probes."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

from netai_chatbot import __version__
from netai_chatbot.config import get_settings
from netai_chatbot.llm.providers import list_providers

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def health_check() -> dict:
    """Liveness probe — is the service running?"""
    return {"status": "ok", "timestamp": datetime.now(UTC).isoformat()}


@router.get("/readyz")
async def readiness_check() -> dict:
    """Readiness probe — is the service ready to accept traffic?"""
    return {
        "status": "ready",
        "timestamp": datetime.now(UTC).isoformat(),
        "version": __version__,
    }


@router.get("/api/v1/info")
async def service_info() -> dict:
    """Service information and available models."""
    settings = get_settings()
    providers = list_providers()

    return {
        "service": "NETAI Chatbot",
        "version": __version__,
        "description": "AI-Powered Kubernetes Chatbot for Network Diagnostics",
        "default_model": settings.llm_default_model.value,
        "available_models": [
            {
                "id": p.model_id,
                "name": p.name,
                "description": p.description,
                "max_context_length": p.max_context_length,
                "supports_vision": p.supports_vision,
                "recommended_for": p.recommended_for,
            }
            for p in providers
        ],
        "endpoints": {
            "chat": "/api/v1/chat/",
            "stream": "/api/v1/chat/stream",
            "conversations": "/api/v1/chat/conversations",
            "network_summary": "/api/v1/network/summary",
            "diagnostics": "/api/v1/network/diagnostics",
            "traceroute": "/api/v1/network/traceroute",
            "health": "/healthz",
            "readiness": "/readyz",
        },
    }
