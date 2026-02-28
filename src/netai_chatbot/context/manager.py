"""Conversation context manager with network telemetry awareness.

Maintains conversation state, injects relevant network context into
LLM prompts, and manages the sliding window of conversation history.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from netai_chatbot.config import Settings, get_settings
from netai_chatbot.diagnostics.telemetry import TelemetryProcessor
from netai_chatbot.llm.prompt_engine import PromptEngine
from netai_chatbot.utils import get_logger

logger = get_logger(__name__)


@dataclass
class Message:
    """A single message in a conversation."""

    role: str  # "user", "assistant", or "system"
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


@dataclass
class Conversation:
    """A conversation session with history and context."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: list[Message] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    network_context: dict = field(default_factory=dict)

    @property
    def message_count(self) -> int:
        return len(self.messages)

    def add_message(self, role: str, content: str, **metadata: str) -> Message:
        msg = Message(role=role, content=content, metadata=metadata)
        self.messages.append(msg)
        return msg

    def get_history(self, max_messages: int | None = None) -> list[dict[str, str]]:
        """Get conversation history as list of dicts for LLM API."""
        msgs = self.messages
        if max_messages:
            msgs = msgs[-max_messages:]
        return [m.to_dict() for m in msgs]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "message_count": self.message_count,
            "created_at": self.created_at.isoformat(),
            "messages": [
                {**m.to_dict(), "timestamp": m.timestamp.isoformat()} for m in self.messages
            ],
        }


class ContextManager:
    """Manages conversation context with network telemetry awareness.

    Handles:
    - Conversation session lifecycle (create, retrieve, delete)
    - Sliding window history management
    - Network telemetry context injection
    - Query classification for optimal prompt selection
    """

    def __init__(
        self,
        prompt_engine: PromptEngine | None = None,
        telemetry: TelemetryProcessor | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.prompt_engine = prompt_engine or PromptEngine()
        self.telemetry = telemetry or TelemetryProcessor()
        self._conversations: dict[str, Conversation] = {}

    def create_conversation(self) -> Conversation:
        """Create a new conversation session."""
        conv = Conversation()
        self._conversations[conv.id] = conv
        logger.info("conversation_created", conversation_id=conv.id)
        return conv

    def get_conversation(self, conversation_id: str) -> Conversation | None:
        """Retrieve an existing conversation by ID."""
        return self._conversations.get(conversation_id)

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and free memory."""
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            logger.info("conversation_deleted", conversation_id=conversation_id)
            return True
        return False

    def list_conversations(self) -> list[dict]:
        """List all active conversation sessions."""
        return [
            {
                "id": c.id,
                "message_count": c.message_count,
                "created_at": c.created_at.isoformat(),
            }
            for c in self._conversations.values()
        ]

    async def build_llm_messages(
        self,
        conversation_id: str,
        user_message: str,
        source: str | None = None,
        destination: str | None = None,
    ) -> list[dict[str, str]]:
        """Build the complete message list for an LLM API call.

        This is the core method that:
        1. Classifies the user query
        2. Selects the optimal prompt template
        3. Retrieves conversation history
        4. Injects network telemetry context
        5. Returns the complete message list
        """
        conv = self.get_conversation(conversation_id)
        if not conv:
            conv = self.create_conversation()
            conv.id = conversation_id  # Use the requested ID

        # Classify query to select best prompt template
        template_name = self.prompt_engine.classify_query(user_message)

        # Get network telemetry context
        telemetry_context = None
        try:
            telemetry_context = await self.telemetry.format_telemetry_context(source, destination)
        except Exception as e:
            logger.warning("telemetry_context_failed", error=str(e))

        # Get conversation history (windowed)
        history = conv.get_history(max_messages=self.settings.context_window_size)

        # Build messages
        messages = self.prompt_engine.build_messages(
            user_message=user_message,
            conversation_history=history,
            template_name=template_name,
            telemetry_context=telemetry_context,
        )

        # Record the user message
        conv.add_message("user", user_message)

        return messages

    def record_assistant_response(self, conversation_id: str, content: str) -> None:
        """Record the assistant's response in conversation history."""
        conv = self.get_conversation(conversation_id)
        if conv:
            conv.add_message("assistant", content)

            # Trim history if it exceeds max
            if conv.message_count > self.settings.max_conversation_history:
                excess = conv.message_count - self.settings.max_conversation_history
                conv.messages = conv.messages[excess:]

    async def close(self) -> None:
        await self.telemetry.close()
