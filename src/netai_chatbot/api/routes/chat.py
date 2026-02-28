"""Chat API routes — core chatbot interaction endpoints."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from netai_chatbot.api.models.chat import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatRole,
    ConversationDetail,
    ConversationInfo,
)
from netai_chatbot.config import LLMModel
from netai_chatbot.context.manager import ContextManager
from netai_chatbot.llm.client import LLMClient
from netai_chatbot.utils import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

# Module-level state (initialized in main.py lifespan)
_llm_client: LLMClient | None = None
_context_manager: ContextManager | None = None


def init_chat_dependencies(llm_client: LLMClient, context_manager: ContextManager) -> None:
    """Initialize chat route dependencies."""
    global _llm_client, _context_manager
    _llm_client = llm_client
    _context_manager = context_manager


def _get_llm() -> LLMClient:
    if not _llm_client:
        raise HTTPException(status_code=503, detail="LLM client not initialized")
    return _llm_client


def _get_ctx() -> ContextManager:
    if not _context_manager:
        raise HTTPException(status_code=503, detail="Context manager not initialized")
    return _context_manager


@router.post("/", response_model=ChatResponse)
async def send_message(request: ChatRequest) -> ChatResponse:
    """Send a message to the NETAI chatbot and receive an AI-powered response.

    The chatbot integrates real-time network telemetry data with LLM reasoning
    to provide intelligent network diagnostics assistance.
    """
    llm = _get_llm()
    ctx = _get_ctx()

    # Create or retrieve conversation
    conv_id = request.conversation_id
    if not conv_id:
        conv = ctx.create_conversation()
        conv_id = conv.id

    # Build context-aware messages
    messages = await ctx.build_llm_messages(
        conversation_id=conv_id,
        user_message=request.message,
        source=request.source,
        destination=request.destination,
    )

    # Select model
    model = None
    if request.model:
        try:
            model = LLMModel(request.model)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid model: {request.model}. Choose from: {[m.value for m in LLMModel]}",
            ) from exc

    # Get LLM response
    try:
        response = await llm.chat_completion(messages=messages, model=model)
    except Exception as e:
        logger.error("chat_completion_failed", error=str(e))
        raise HTTPException(status_code=502, detail=f"LLM service error: {e!s}") from e

    # Record response in conversation history
    ctx.record_assistant_response(conv_id, response.content)

    return ChatResponse(
        conversation_id=conv_id,
        message=ChatMessage(
            role=ChatRole.ASSISTANT,
            content=response.content,
            timestamp=datetime.now(UTC),
        ),
        model=response.model,
        usage=response.usage,
    )


@router.post("/stream")
async def stream_message(request: ChatRequest) -> StreamingResponse:
    """Stream a chatbot response token by token using Server-Sent Events."""
    llm = _get_llm()
    ctx = _get_ctx()

    conv_id = request.conversation_id
    if not conv_id:
        conv = ctx.create_conversation()
        conv_id = conv.id

    messages = await ctx.build_llm_messages(
        conversation_id=conv_id,
        user_message=request.message,
        source=request.source,
        destination=request.destination,
    )

    model = None
    if request.model:
        try:
            model = LLMModel(request.model)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid model: {request.model}") from exc

    async def generate():
        full_response = ""
        try:
            async for token in llm.stream_completion(messages=messages, model=model):
                full_response += token
                yield f"data: {token}\n\n"
            yield "data: [DONE]\n\n"
            ctx.record_assistant_response(conv_id, full_response)
        except Exception as e:
            yield f"data: [ERROR] {e!s}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/conversations", response_model=list[ConversationInfo])
async def list_conversations() -> list[ConversationInfo]:
    """List all active conversation sessions."""
    ctx = _get_ctx()
    convs = ctx.list_conversations()
    return [ConversationInfo(**c) for c in convs]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(conversation_id: str) -> ConversationDetail:
    """Get full conversation history."""
    ctx = _get_ctx()
    conv = ctx.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationDetail(
        id=conv.id,
        message_count=conv.message_count,
        created_at=conv.created_at,
        messages=[
            ChatMessage(
                role=ChatRole(m.role),
                content=m.content,
                timestamp=m.timestamp,
            )
            for m in conv.messages
        ],
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str) -> dict:
    """Delete a conversation session."""
    ctx = _get_ctx()
    if ctx.delete_conversation(conversation_id):
        return {"status": "deleted", "conversation_id": conversation_id}
    raise HTTPException(status_code=404, detail="Conversation not found")
