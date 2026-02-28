"""Tests for conversation context manager."""

from __future__ import annotations

import pytest

from netai_chatbot.context.manager import ContextManager, Conversation


def test_create_conversation(context_manager: ContextManager) -> None:
    """Test creating a new conversation."""
    conv = context_manager.create_conversation()
    assert isinstance(conv, Conversation)
    assert conv.id
    assert conv.message_count == 0


def test_get_conversation(context_manager: ContextManager) -> None:
    """Test retrieving an existing conversation."""
    conv = context_manager.create_conversation()
    retrieved = context_manager.get_conversation(conv.id)
    assert retrieved is not None
    assert retrieved.id == conv.id


def test_get_nonexistent_conversation(context_manager: ContextManager) -> None:
    """Test retrieving a non-existent conversation returns None."""
    assert context_manager.get_conversation("nonexistent") is None


def test_delete_conversation(context_manager: ContextManager) -> None:
    """Test deleting a conversation."""
    conv = context_manager.create_conversation()
    assert context_manager.delete_conversation(conv.id)
    assert context_manager.get_conversation(conv.id) is None


def test_delete_nonexistent_conversation(context_manager: ContextManager) -> None:
    """Test deleting a non-existent conversation returns False."""
    assert not context_manager.delete_conversation("nonexistent")


def test_list_conversations(context_manager: ContextManager) -> None:
    """Test listing all conversations."""
    context_manager.create_conversation()
    context_manager.create_conversation()
    convs = context_manager.list_conversations()
    assert len(convs) >= 2


@pytest.mark.asyncio
async def test_build_llm_messages(context_manager: ContextManager) -> None:
    """Test building LLM messages with context."""
    conv = context_manager.create_conversation()
    messages = await context_manager.build_llm_messages(
        conversation_id=conv.id,
        user_message="What is the throughput?",
    )
    assert len(messages) >= 2  # system + user at minimum
    assert messages[0]["role"] == "system"
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == "What is the throughput?"


@pytest.mark.asyncio
async def test_build_llm_messages_with_network_context(
    context_manager: ContextManager,
) -> None:
    """Test building messages with network endpoint context."""
    conv = context_manager.create_conversation()
    messages = await context_manager.build_llm_messages(
        conversation_id=conv.id,
        user_message="Check the path",
        source="sdsc-prp.ucsd.edu",
        destination="nrp-chi.uchicago.edu",
    )
    # System prompt should contain telemetry context
    system_msg = messages[0]["content"]
    assert "sdsc-prp.ucsd.edu" in system_msg or "Network" in system_msg


def test_record_assistant_response(context_manager: ContextManager) -> None:
    """Test recording assistant responses."""
    conv = context_manager.create_conversation()
    conv.add_message("user", "Hello")
    context_manager.record_assistant_response(conv.id, "Hi there!")

    assert conv.message_count == 2
    assert conv.messages[-1].role == "assistant"
    assert conv.messages[-1].content == "Hi there!"


def test_conversation_history_windowing(context_manager: ContextManager) -> None:
    """Test that conversation history is windowed correctly."""
    conv = context_manager.create_conversation()

    # Add many messages
    for i in range(20):
        conv.add_message("user", f"Message {i}")
        conv.add_message("assistant", f"Response {i}")

    # Get windowed history
    history = conv.get_history(max_messages=10)
    assert len(history) == 10


def test_conversation_to_dict(context_manager: ContextManager) -> None:
    """Test conversation serialization."""
    conv = context_manager.create_conversation()
    conv.add_message("user", "Hello")
    conv.add_message("assistant", "Hi!")

    d = conv.to_dict()
    assert d["id"] == conv.id
    assert d["message_count"] == 2
    assert len(d["messages"]) == 2
