"""ReAct Framework Entry Point"""
import logging
from typing import Callable, Optional

from .config.setting import Settings
from .mcp.client.manager import MCPClientManager
from .mcp.tool.registry import ToolRegistry
from .core.engine.engine import ReActEngine
from .llm.client import LLMClient
from .model.response import ResponseData
from .util.exception import AgentException

logger = logging.getLogger(__name__)


class ReActAgent:
    """
    ReAct Agent

    Integrates LLM, MCP tools, and reasoning engine
    """

    def __init__(self, settings: Settings) -> None:
        """
        Initialize the agent

        :param settings: Configuration
        """
        self.settings = settings
        self.mcp_manager: Optional[MCPClientManager] = None
        self.tool_registry: Optional[ToolRegistry] = None
        self._llm_client: Optional[LLMClient] = None
        self.engine: Optional[ReActEngine] = None

    async def initialize(self) -> None:
        """Initialize the framework"""
        self._init_llm_client()

        await self._init_mcp()
        await self._init_engine()

    def _init_llm_client(self) -> None:
        """Initialize LLM client"""
        if not self.settings.llm_config:
            return

        try:
            # Import all LLM provider modules to register their clients
            import react.llm.openai  # noqa: F401
            import react.llm.vllm    # noqa: F401

            provider = self.settings.llm_config.provider
            logger.info(f"Initializing LLM client for provider: {provider}")

            # Log available providers
            from react.llm.client import LLMClientFactory
            available = LLMClientFactory.list_providers()
            logger.info(f"Available providers: {available}")

            self._llm_client = LLMClientFactory.create(self.settings.llm_config)
            logger.info(f"Successfully created LLM client: {type(self._llm_client).__name__}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}", exc_info=True)
            self._llm_client = None

    async def _init_mcp(self) -> None:
        """Initialize MCP"""
        if not self.settings.mcp_config or not self.settings.mcp_config.servers:
            self.tool_registry = ToolRegistry()
            return

        self.mcp_manager = MCPClientManager(self.settings.mcp_config)
        await self.mcp_manager.initialize()

        # MCPClientManager.initialize() already calls refresh_tools() internally
        self.tool_registry = self.mcp_manager._tool_registry

    async def _init_engine(self) -> None:
        """Initialize reasoning engine"""
        self.engine = ReActEngine(
            llm_client=self.llm_client,
            mcp_manager=self.mcp_manager,
            config=self.settings,
            react_config=self.settings.react_config
        )

        if self.tool_registry:
            tools = self.tool_registry.get_all_tools()
            self.engine.update_tools(tools)

    @property
    def llm_client(self) -> LLMClient:
        if self._llm_client is None:
            raise ConnectionError(
                'llm-client not initialized, '
                'please execute ReactAgent.initialize() first'
            )
        return self._llm_client

    async def query(
        self,
        question: str,
        stream_callback: Optional[Callable[[ResponseData], None]] = None
    ) -> str:
        """
        Execute query

        :param question: Question
        :param stream_callback: Stream callback function receiving ResponseData
        :return: Answer
        """
        if not self.engine:
            raise AgentException("Agent not initialized")

        result = await self.engine.execute(question, stream_callback)
        return result.answer

    async def close(self) -> None:
        """Close resources"""

        if self._llm_client:
            await self._llm_client.close()

        if self.mcp_manager:
            await self.mcp_manager.close()
