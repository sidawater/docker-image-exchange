"""
Chat router

Provides chat-related API endpoints, including:
1. Chat completion
2. Session management
3. Chat history
4. Batch chat
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from init.msg.models import (
    ChatSessionOut,
    ChatHistoryOut,
    BatchChatResponse
)
from .handle import (
    chat_completion,
    create_session,
    get_session,
    update_session,
    get_history,
    batch_chat
)


router = APIRouter(prefix="/chat", tags=["chat"])


router.add_api_route(
    path="/completions",
    endpoint=chat_completion,
    methods=["POST"],
    response_class=StreamingResponse,
    summary="Chat completion endpoint",
    description="""Chat interface based on ReAct framework with streaming response and session management.

Supports two response modes:
1. Streaming response (SSE): Real-time AI thinking process, tool calls, and generated content
2. Non-streaming response: Complete result returned at once (not yet implemented)

SSE message types:
- thinking: AI thinking process
- content: Generated content
- tool-call: Tool invocation
- tool-result: Tool results
- error: Error information
- status: Status updates
- metadata: Metadata
"""
)

router.add_api_route(
    path="/sessions",
    endpoint=create_session,
    methods=["POST"],
    response_model=ChatSessionOut,
    summary="Create chat session",
    description="Create a new chat session with optional ReAct instance specification"
)

router.add_api_route(
    path="/sessions/{session_id}",
    endpoint=get_session,
    methods=["GET"],
    response_model=ChatSessionOut,
    summary="Get chat session",
    description="Get detailed information of a specific chat session"
)

router.add_api_route(
    path="/sessions/{session_id}",
    endpoint=update_session,
    methods=["PUT"],
    response_model=ChatSessionOut,
    summary="Update chat session",
    description="Update session title, status, or metadata"
)

router.add_api_route(
    path="/history",
    endpoint=get_history,
    methods=["POST"],
    response_model=ChatHistoryOut,
    summary="Get chat history",
    description="Get chat history for a session with pagination and sorting support"
)

router.add_api_route(
    path="/batch",
    endpoint=batch_chat,
    methods=["POST"],
    response_model=BatchChatResponse,
    summary="Batch chat",
    description="Process multiple chat requests in parallel or serial mode"
)
