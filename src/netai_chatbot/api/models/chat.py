"""Chat request and response models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ChatRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=4096,
        description="User's message to the chatbot",
        examples=["What's the throughput between San Diego and Chicago?"],
    )
    conversation_id: str | None = Field(
        default=None,
        description="Conversation session ID. If None, a new conversation is created.",
    )
    model: str | None = Field(
        default=None,
        description="LLM model override (qwen3-vl, glm-4.7, gpt-oss)",
    )
    source: str | None = Field(
        default=None,
        description="Network source endpoint for context",
        examples=["sdsc-prp.ucsd.edu"],
    )
    destination: str | None = Field(
        default=None,
        description="Network destination endpoint for context",
        examples=["nrp-chi.uchicago.edu"],
    )
    stream: bool = Field(
        default=False,
        description="Whether to stream the response",
    )


class ChatMessage(BaseModel):
    """A single chat message."""

    role: ChatRole
    content: str
    timestamp: datetime | None = None


class ChatResponse(BaseModel):
    """Response body for chat endpoint."""

    conversation_id: str
    message: ChatMessage
    model: str
    usage: dict[str, int] = Field(default_factory=dict)
    network_context: dict | None = None


class ConversationInfo(BaseModel):
    """Summary info for a conversation session."""

    id: str
    message_count: int
    created_at: datetime


class ConversationDetail(BaseModel):
    """Full conversation with message history."""

    id: str
    message_count: int
    created_at: datetime
    messages: list[ChatMessage]
