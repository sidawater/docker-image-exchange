"""
Chat handler

Handles chat requests with support for:
1. ReAct framework-based reasoning
2. SSE streaming responses
3. Session management
4. QA record management
5. Chat history queries
6. Batch chat
"""

import asyncio
import logging
from typing import Optional, Dict, Any, AsyncGenerator
import json

from fastapi import HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from react.manager import react_manager, ManagedReActInstance
from react.config.llm import LLMConfig
from react.config.mcp import MCPConfig
from init.msg import get_msg_manager
from init.msg.exceptions import NotFoundError
from init.msg.models import (
    SessionCreateRequest,
    SessionUpdateRequest,
    QaCreateRequest,
    QaUpdateRequest,
    QaMessageContent,
    QaSearchParams,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatSessionCreateRequest,
    ChatSessionUpdateRequest,
    ChatSessionOut,
    ChatHistoryRequest,
    ChatHistoryOut,
    ChatMessage,
    BatchChatRequest,
    BatchChatResponse,
)
from init.db.postgres import db
from init.utils.json import DefaultEncoder
from structure.models.react import ReActInstance as ReActInstanceModel
from react.model.response import MessageType, ResponseData

logger = logging.getLogger(__name__)


class ChatHandler:
    """Chat handler"""

    async def handle_chat(self, request: ChatCompletionRequest) -> StreamingResponse:
        """
        Handle chat request

        :param request: Chat request
        :return: SSE streaming response
        """
        logger.info(
            f"Received chat request: session_id={request.session_id}, "
            f"react_code={request.react_instance_code}, "
            f"message={request.message[:50]}..."
        )

        session_id = await self._ensure_session(request.session_id)
        qa_id = self._create_qa_record(session_id, request.message)
        react_instance = await self._get_or_create_react_instance(
            request.react_instance_code
        )

        return StreamingResponse(
            self._stream_chat_response(
                react_instance,
                request.message,
                qa_id
            ),
            media_type="text/event-stream"
        )

    async def _ensure_session(self, session_id: str) -> str:
        """
        Ensure session exists, create if not found

        :param session_id: Session ID
        :return: Session ID
        """
        session_client = get_msg_manager().client.sessions

        try:
            session_client.get(session_id)
        except NotFoundError:
            session_client.create(SessionCreateRequest(
                user_id=session_id,
                title=f"Chat Session {session_id}"
            ))
        return session_id

    def _create_qa_record(self, session_id: str, message: str) -> str:
        """
        Create QA record

        :param session_id: Session ID
        :param message: User message
        :return: QA record ID
        """
        qa_client = get_msg_manager().client.qa
        qa_request = QaCreateRequest(
            session_id=session_id,
            qa_key=f"chat_{session_id}",
            question=QaMessageContent(content=message),
            answer=QaMessageContent(content="")
        )
        result = qa_client.create(qa_request)
        return result.get("id", "")

    async def _get_or_create_react_instance(
        self,
        code: str
    ) -> Any:
        """
        Get or create ReAct instance

        :param code: Instance code
        :return: ReAct instance
        """
        config = await self._get_react_instance_config(code)
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"ReAct instance configuration not found: {code}"
            )

        llm_config = self._build_llm_config(config.get("llm", {}))
        mcp_config = self._build_mcp_config(config.get("mcp", {}))

        existing = await react_manager.get_instance(code)
        if existing:
            existing_llm = existing.llm_config
            if (existing_llm.base_url == llm_config.base_url and
                existing_llm.model == llm_config.model and
                existing_llm.api_key == llm_config.api_key):
                logger.info(f"Using existing ReAct instance: {code}")
                return existing
            else:
                logger.warning(f"ReAct instance {code} configuration mismatch, destroying and recreating")
                await react_manager.destroy_instance(code)

        await react_manager.initialize()
        instance = await react_manager.create_instance(
            instance_id=code,
            llm_config=llm_config,
            mcp_config=mcp_config
        )

        logger.info(f"Successfully created ReAct instance: {code}")
        return instance

    async def _get_react_instance_config(
        self,
        code: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get ReAct instance configuration

        :param code: Instance code
        :return: Configuration dictionary or None
        """
        async with db.get_session() as session:
            stmt = select(ReActInstanceModel).where(
                ReActInstanceModel.code == code,
                ReActInstanceModel.is_enabled == True
            )
            result = await session.execute(stmt)
            instance = result.scalar_one_or_none()

            if instance is None:
                logger.warning(f"ReAct instance does not exist or is not enabled: {code}")
                return None

            return await instance.to_meta_react_config()

    def _build_llm_config(self, config: Dict[str, Any]) -> LLMConfig:
        """
        Build LLM configuration

        :param config: Configuration dictionary
        :return: LLMConfig object
        """
        logger.info(f"Raw LLM configuration: {config}")

        if not config.get("provider"):
            raise ValueError("LLM configuration error: provider cannot be empty")

        if not config.get("model"):
            raise ValueError("LLM configuration error: model cannot be empty")

        llm_config = LLMConfig(
            provider=config["provider"],
            model=config["model"],
            api_key=config.get("api_key", ""),
            base_url=config.get("base_url"),
            temperature=config.get("temperature", 0.1),
            max_tokens=config.get("max_tokens", 4096)
        )
        logger.info(f"Built LLM configuration: provider={llm_config.provider}, model={llm_config.model}, base_url={llm_config.base_url}")
        return llm_config

    def _build_mcp_config(self, config: Dict[str, Any]) -> MCPConfig:
        """
        Build MCP configuration

        :param config: Configuration dictionary
        :return: MCPConfig object
        """
        servers = []
        for server_data in config.get("servers", []):
            if not server_data.get("name"):
                raise ValueError("MCP configuration error: server.name cannot be empty")

            servers.append(MCPConfig.Server(
                name=server_data["name"],
                type=server_data.get("type", ""),
                command=server_data.get("command"),
                url=server_data.get("url"),
                args=server_data.get("args", []),
                headers=server_data.get("headers"),
                auth_token=server_data.get("auth_token"),
                timeout=server_data.get("timeout", 30),
                reconnect_attempts=server_data.get("reconnect_attempts", 3)
            ))

        return MCPConfig(
            servers=servers,
            connection_timeout=config.get("connection_timeout", 30),
            reconnect_attempts=config.get("reconnect_attempts", 3)
        )

    async def _stream_chat_response(
        self,
        react_instance: 'ManagedReActInstance',
        message: str,
        qa_id: str
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response

        :param react_instance: ReAct instance
        :param message: User message
        :param qa_id: QA record ID
        :return: SSE message stream
        """
        full_response = [""]
        queue = asyncio.Queue()

        yield f"data: {json.dumps({'type': 'status', 'data': 'Starting request processing'})}\n\n"

        async def stream_callback(response_data: 'ResponseData') -> None:
            logger.info(f"Stream output: {response_data.message_type.value} - {response_data.data}")
            await queue.put(response_data)

        task = asyncio.create_task(self._run_react_query(
            react_instance=react_instance,
            message=message,
            stream_callback=stream_callback,
            queue=queue
        ))

        async for msg in self._process_stream_messages(
            queue=queue,
            task=task,
            full_response=full_response
        ):
            yield msg

        await task
        self._update_qa_record(qa_id=qa_id, answer=full_response[0])
        yield f"data: {json.dumps({'type': 'status', 'data': {'finish': True}})}\n\n"

    async def _process_stream_messages(
        self,
        queue: asyncio.Queue,
        task: asyncio.Task,
        full_response: list[str]
    ) -> AsyncGenerator[str, None]:
        """
        Process messages from stream queue

        :param queue: Message queue
        :param task: ReAct query task
        :param full_response: Response string accumulator (list with one element)
        :return: SSE message stream
        """
        while True:
            try:
                response_data = await asyncio.wait_for(queue.get(), timeout=1.0)

                if isinstance(response_data, Exception):
                    yield f"data: {json.dumps({'type': 'error', 'content': f'Error processing response: {str(response_data)}'})}\n\n"
                    break

                if isinstance(response_data, str):
                    full_response[0] = response_data
                    break

                if isinstance(response_data, ResponseData):
                    if response_data.message_type == MessageType.CONTENT:
                        full_response[0] += str(response_data.data)
                    for msg in self._process_response_message(response_data):
                        yield msg

            except asyncio.TimeoutError:
                if task.done():
                    break
                continue

    async def _run_react_query(
        self,
        react_instance: 'ManagedReActInstance',
        message: str,
        stream_callback,
        queue: asyncio.Queue
    ) -> None:
        """
        Run ReAct query in background task

        :param react_instance: ReAct instance
        :param message: User message
        :param stream_callback: Stream callback function
        :param queue: Queue for communication
        """
        result = await react_instance.agent.query(message, stream_callback=stream_callback)
        await queue.put(result)

    def _process_response_message(self, response_data: 'ResponseData') -> list[str]:
        """
        Process response message and return SSE data

        :param response_data: Response data
        :return: List of SSE messages
        """
        msg_type = response_data.message_type
        data = response_data.data

        if msg_type == MessageType.CONTENT:
            return [f"data: {json.dumps({'type': 'content', 'data': data}, ensure_ascii=False, cls=DefaultEncoder)}\n\n"]
        elif msg_type == MessageType.THINKING:
            return [f"data: {json.dumps({'type': 'thinking', 'data': data}, ensure_ascii=False, cls=DefaultEncoder)}\n\n"]
        elif msg_type == MessageType.TOOL_RESULT:
            return [f"data: {json.dumps({'type': 'tool-result', 'data': data}, ensure_ascii=False, cls=DefaultEncoder)}\n\n"]
        elif msg_type == MessageType.STATUS:
            return [f"data: {json.dumps({'type': 'status', 'data': data}, ensure_ascii=False, cls=DefaultEncoder)}\n\n"]
        elif msg_type == MessageType.ERROR:
            return [f"data: {json.dumps({'type': 'error', 'data': data}, ensure_ascii=False, cls=DefaultEncoder)}\n\n"]
        elif msg_type == MessageType.TOOL_CALL:
            return [f"data: {json.dumps({'type': 'tool-call', 'data': data}, ensure_ascii=False, cls=DefaultEncoder)}\n\n"]
        return []

    def _update_qa_record(self, qa_id: str, answer: str) -> None:
        """
        Update QA record

        :param qa_id: QA record ID
        :param answer: Answer content
        """
        if not qa_id:
            return

        qa_client = get_msg_manager().client.qa
        qa_update = QaUpdateRequest(
            answer=QaMessageContent(content=answer)
        )
        qa_client.update(qa_id, qa_update)
        logger.info(f"QA record updated successfully: {qa_id}")

    async def create_chat_session(
        self,
        request: ChatSessionCreateRequest
    ) -> ChatSessionOut:
        """
        Create chat session

        :param request: Create session request
        :return: Session information
        """
        session_id = f"session_{request.user_id}_{int(asyncio.get_event_loop().time())}"
        session_request = SessionCreateRequest(
            user_id=request.user_id,
            title=request.title or f"Chat Session {session_id}",
            metadata={
                "react_instance_code": request.react_instance_code,
                **(request.metadata or {})
            }
        )

        session_client = get_msg_manager().client.sessions
        result = session_client.create(session_request)

        logger.info(f"Chat session created successfully: {session_id}")
        return ChatSessionOut(
            session_id=result.get("session_id", session_id),
            user_id=request.user_id,
            title=request.title or f"Chat Session {session_id}",
            is_active=True,
            react_instance_code=request.react_instance_code,
            message_count=0,
            metadata=request.metadata,
            tags=request.tags,
            create_time=result.get("create_time", ""),
            update_time=result.get("update_time", "")
        )

    async def get_chat_session(self, session_id: str) -> ChatSessionOut:
        """
        Get chat session information

        :param session_id: Session ID
        :return: Session information
        """
        session_client = get_msg_manager().client.sessions
        result = session_client.get(session_id)

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Session not found: {session_id}"
            )

        metadata = result.get("metadata", {})
        return ChatSessionOut(
            session_id=session_id,
            user_id=result.get("user_id", ""),
            title=result.get("title"),
            is_active=result.get("is_active", True),
            react_instance_code=metadata.get("react_instance_code", ""),
            message_count=0,
            metadata=metadata,
            tags=metadata.get("tags", []),
            create_time=result.get("create_time", ""),
            update_time=result.get("update_time", "")
        )

    async def update_chat_session(
        self,
        session_id: str,
        request: ChatSessionUpdateRequest
    ) -> ChatSessionOut:
        """
        Update chat session

        :param session_id: Session ID
        :param request: Update session request
        :return: Updated session information
        """
        session_client = get_msg_manager().client.sessions
        result = session_client.get(session_id)

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Session not found: {session_id}"
            )

        update_data = SessionUpdateRequest()
        if request.title is not None:
            update_data.title = request.title
        if request.is_active is not None:
            update_data.is_active = request.is_active
        if request.metadata is not None:
            update_data.metadata = request.metadata
        if request.tags is not None:
            update_data.metadata = {
                **(result.get("metadata", {})),
                "tags": request.tags
            }

        session_client.update(session_id, update_data)

        logger.info(f"Chat session updated successfully: {session_id}")
        return await self.get_chat_session(session_id)

    async def get_chat_history(
        self,
        request: ChatHistoryRequest
    ) -> ChatHistoryOut:
        """
        Get chat history

        :param request: Chat history request
        :return: Chat history
        """
        qa_client = get_msg_manager().client.qa
        search_params = QaSearchParams(
            session_id=request.session_id,
            offset=request.offset,
            limit=request.limit
        )

        result = qa_client.search(search_params)
        items = result.get("items", [])

        messages = []
        for item in items:
            messages.append(ChatMessage(
                role="user",
                content=item.get("question", {}).get("content", ""),
                timestamp=item.get("create_time")
            ))
            messages.append(ChatMessage(
                role="assistant",
                content=item.get("answer", {}).get("content", ""),
                timestamp=item.get("update_time")
            ))

        return ChatHistoryOut(
            session_id=request.session_id,
            total=result.get("total", 0),
            messages=messages
        )

    async def batch_chat(
        self,
        request: BatchChatRequest
    ) -> BatchChatResponse:
        """
        Batch chat

        :param request: Batch chat request
        :return: Batch chat response
        """
        if request.parallel:
            tasks = [self._process_single_request(req) for req in request.requests]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            results = []
            for req in request.requests:
                result = await self._process_single_request(req)
                results.append(result)

        success_count = sum(1 for r in results if isinstance(r, ChatCompletionResponse))
        failed_count = len(results) - success_count

        logger.info(f"Batch chat completed: success={success_count}, failed={failed_count}")

        return BatchChatResponse(
            results=[r for r in results if isinstance(r, ChatCompletionResponse)],
            success_count=success_count,
            failed_count=failed_count
        )

    async def _process_single_request(
        self,
        request_item: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """
        Process a single chat request in batch mode

        :param request_item: Chat completion request
        :return: Chat completion response
        """
        session_id = await self._ensure_session(request_item.session_id)
        qa_id = self._create_qa_record(session_id, request_item.message)
        react_instance = await self._get_or_create_react_instance(
            request_item.react_instance_code
        )

        full_response = await self._collect_stream_response(
            react_instance,
            request_item.message
        )

        self._update_qa_record(qa_id, full_response)

        return ChatCompletionResponse(
            session_id=session_id,
            message_id=qa_id,
            content=full_response,
            metadata=request_item.metadata,
            create_time=""
        )

    async def _collect_stream_response(
        self,
        react_instance: 'ManagedReActInstance',
        message: str
    ) -> str:
        """
        Collect response from streaming ReAct instance

        :param react_instance: ReAct instance
        :param message: User message
        :return: Complete response string
        """
        full_response = ""
        queue = asyncio.Queue()

        async def stream_callback(response_data: 'ResponseData') -> None:
            await queue.put(response_data)

        task = asyncio.create_task(
            self._run_react_query(react_instance, message, stream_callback, queue)
        )

        while True:
            try:
                response_data = await asyncio.wait_for(queue.get(), timeout=1.0)

                if isinstance(response_data, Exception):
                    raise Exception(str(response_data))

                if isinstance(response_data, str):
                    full_response = response_data
                    break

                if isinstance(response_data, ResponseData):
                    if response_data.message_type == MessageType.CONTENT:
                        full_response += str(response_data.data)
                    elif response_data.message_type == MessageType.STATUS:
                        pass
                    elif response_data.message_type == MessageType.ERROR:
                        raise Exception(str(response_data.data))

            except asyncio.TimeoutError:
                if task.done():
                    break

        await task
        return full_response


def get_chat_handler() -> ChatHandler:
    """
    Get chat handler

    :return: ChatHandler instance
    """
    return ChatHandler()


async def chat_completion(
    message: str = Query(..., description="User message"),
    session_id: str = Query(..., description="Session ID"),
    stream: bool = Query(True, description="Enable streaming response"),
    react_instance_code: str = Query(..., description="ReAct instance code")
):
    """
    Chat completion endpoint

    :param message: User message
    :param session_id: Session ID (required)
    :param stream: Enable streaming response (default: true)
    :param react_instance_code: ReAct instance code (required)
    :return: SSE streaming response or JSON response
    """
    chat_request = ChatCompletionRequest(
        message=message,
        session_id=session_id,
        stream=stream,
        react_instance_code=react_instance_code
    )

    chat_handler = get_chat_handler()
    return await chat_handler.handle_chat(chat_request)


async def create_session(request: ChatSessionCreateRequest):
    """
    Create chat session

    :param request: Create session request
    :return: Session information
    """
    chat_handler = get_chat_handler()
    return await chat_handler.create_chat_session(request)


async def get_session(session_id: str):
    """
    Get chat session

    :param session_id: Session ID
    :return: Session information
    """
    chat_handler = get_chat_handler()
    return await chat_handler.get_chat_session(session_id)


async def update_session(
    session_id: str,
    request: ChatSessionUpdateRequest
):
    """
    Update chat session

    :param session_id: Session ID
    :param request: Update session request
    :return: Updated session information
    """
    chat_handler = get_chat_handler()
    return await chat_handler.update_chat_session(session_id, request)


async def get_history(request: ChatHistoryRequest):
    """
    Get chat history

    :param request: Chat history request
    :return: Chat history
    """
    chat_handler = get_chat_handler()
    return await chat_handler.get_chat_history(request)


async def batch_chat(request: BatchChatRequest):
    """
    Batch chat

    :param request: Batch chat request
    :return: Batch chat response
    """
    chat_handler = get_chat_handler()
    return await chat_handler.batch_chat(request)
