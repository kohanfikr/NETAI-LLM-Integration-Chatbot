"""Tests for chat API endpoints."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_send_message(async_client: AsyncClient) -> None:
    """Test sending a message and receiving a response."""
    response = await async_client.post(
        "/api/v1/chat/",
        json={"message": "What is the current throughput?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "conversation_id" in data
    assert "message" in data
    assert data["message"]["role"] == "assistant"
    assert len(data["message"]["content"]) > 0
    assert "model" in data


@pytest.mark.asyncio
async def test_send_message_with_model(async_client: AsyncClient) -> None:
    """Test sending a message with a specific model."""
    response = await async_client.post(
        "/api/v1/chat/",
        json={"message": "Check latency", "model": "glm-4.7"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "glm-4.7"


@pytest.mark.asyncio
async def test_send_message_invalid_model(async_client: AsyncClient) -> None:
    """Test sending a message with an invalid model."""
    response = await async_client.post(
        "/api/v1/chat/",
        json={"message": "Hello", "model": "invalid-model"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_send_message_with_network_context(async_client: AsyncClient) -> None:
    """Test sending a message with network source/destination context."""
    response = await async_client.post(
        "/api/v1/chat/",
        json={
            "message": "What is the throughput?",
            "source": "sdsc-prp.ucsd.edu",
            "destination": "nrp-chi.uchicago.edu",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "throughput" in data["message"]["content"].lower() or len(data["message"]["content"]) > 0


@pytest.mark.asyncio
async def test_conversation_persistence(async_client: AsyncClient) -> None:
    """Test that conversation state persists across messages."""
    # First message
    resp1 = await async_client.post(
        "/api/v1/chat/",
        json={"message": "Hello"},
    )
    assert resp1.status_code == 200
    conv_id = resp1.json()["conversation_id"]

    # Second message in same conversation
    resp2 = await async_client.post(
        "/api/v1/chat/",
        json={"message": "Follow up question about throughput", "conversation_id": conv_id},
    )
    assert resp2.status_code == 200
    assert resp2.json()["conversation_id"] == conv_id


@pytest.mark.asyncio
async def test_list_conversations(async_client: AsyncClient) -> None:
    """Test listing conversation sessions."""
    # Create a conversation first
    await async_client.post(
        "/api/v1/chat/",
        json={"message": "Start a conversation"},
    )

    response = await async_client.get("/api/v1/chat/conversations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


@pytest.mark.asyncio
async def test_get_conversation(async_client: AsyncClient) -> None:
    """Test retrieving a specific conversation."""
    # Create conversation
    resp = await async_client.post(
        "/api/v1/chat/",
        json={"message": "Test message"},
    )
    conv_id = resp.json()["conversation_id"]

    # Get conversation
    response = await async_client.get(f"/api/v1/chat/conversations/{conv_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == conv_id
    assert data["message_count"] >= 1


@pytest.mark.asyncio
async def test_get_nonexistent_conversation(async_client: AsyncClient) -> None:
    """Test retrieving a conversation that doesn't exist."""
    response = await async_client.get("/api/v1/chat/conversations/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_conversation(async_client: AsyncClient) -> None:
    """Test deleting a conversation."""
    # Create conversation
    resp = await async_client.post(
        "/api/v1/chat/",
        json={"message": "To be deleted"},
    )
    conv_id = resp.json()["conversation_id"]

    # Delete it
    response = await async_client.delete(f"/api/v1/chat/conversations/{conv_id}")
    assert response.status_code == 200

    # Verify it's gone
    response = await async_client.get(f"/api/v1/chat/conversations/{conv_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_empty_message_rejected(async_client: AsyncClient) -> None:
    """Test that empty messages are rejected."""
    response = await async_client.post(
        "/api/v1/chat/",
        json={"message": ""},
    )
    assert response.status_code == 422
