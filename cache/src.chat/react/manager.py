"""
ReAct Instance Manager

Provides functionality for creating, retrieving, and destroying ReAct instances
"""

import asyncio
from typing import Dict, Optional, List, Any
from dataclasses import dataclass

from react.api import ReActAgent
from react.config.setting import Settings
from react.config.llm import LLMConfig
from react.config.mcp import MCPConfig
from react.config.react import ReActConfig


@dataclass
class ManagedReActInstance:
    """Managed ReAct Instance"""
    instance_id: str
    agent: ReActAgent
    llm_config: LLMConfig
    mcp_config: MCPConfig
    react_config: Optional[ReActConfig]
    created_at: float
    last_used: Optional[float] = None
    use_count: int = 0


class ReActManager:
    """
    ReAct Instance Manager

    Responsibilities:
    1. Manage the creation, retrieval, and destruction of ReAct instances
    2. Support initializing instances by configuration groups
    3. Provide lazy loading and caching mechanism for instances
    """

    def __init__(self):
        """Initialize the manager"""
        self._instances: Dict[str, ManagedReActInstance] = {}
        self._initialized = False
        self._init_lock = asyncio.Lock()

    async def initialize(self) -> None:
        """
        Initialize the manager

        Only sets the initialization state, does not load any instances
        """
        async with self._init_lock:
            if self._initialized:
                return

            self._initialized = True

    async def create_instance(
        self,
        instance_id: str,
        llm_config: LLMConfig,
        mcp_config: MCPConfig,
        react_config: Optional[ReActConfig] = None
    ) -> ManagedReActInstance:
        """
        Create and get a ReAct instance

        If the instance already exists, return the existing instance directly

        :param instance_id: Instance ID
        :param llm_config: LLM configuration
        :param mcp_config: MCP configuration
        :param react_config: ReAct engine configuration
        :return: Managed instance
        """
        if not self._initialized:
            raise RuntimeError("ReAct manager not initialized")

        if instance_id in self._instances:
            existing_instance = self._instances[instance_id]
            if (existing_instance.llm_config == llm_config and
                existing_instance.mcp_config == mcp_config):
                existing_instance.last_used = asyncio.get_event_loop().time()
                existing_instance.use_count += 1
                return existing_instance
            else:
                await self.destroy_instance(instance_id)

        try:
            settings = Settings(
                llm_config=llm_config,
                mcp_config=mcp_config,
                react_config=react_config
            )

            agent = ReActAgent(settings)
            await agent.initialize()

            managed_instance = ManagedReActInstance(
                instance_id=instance_id,
                agent=agent,
                llm_config=llm_config,
                mcp_config=mcp_config,
                react_config=react_config,
                created_at=asyncio.get_event_loop().time(),
                last_used=asyncio.get_event_loop().time(),
                use_count=1
            )

            self._instances[instance_id] = managed_instance
            return managed_instance

        except Exception as e:
            raise

    async def get_instance(self, instance_id: str) -> Optional[ManagedReActInstance]:
        """
        Get an initialized ReAct instance

        :param instance_id: Instance ID
        :return: Managed instance, returns None if not exists
        """
        if not self._initialized:
            return None

        instance = self._instances.get(instance_id)
        if instance:
            instance.last_used = asyncio.get_event_loop().time()
            instance.use_count += 1

        return instance

    async def get_or_create_instance(
        self,
        instance_id: str,
        llm_config: LLMConfig,
        mcp_config: MCPConfig
    ) -> ManagedReActInstance:
        """
        Get an initialized instance, create if it doesn't exist

        :param instance_id: Instance ID
        :param llm_config: LLM configuration
        :param mcp_config: MCP configuration
        :return: Managed instance
        """
        existing_instance = await self.get_instance(instance_id)
        if existing_instance:
            return existing_instance

        return await self.create_instance(instance_id, llm_config, mcp_config)

    async def get_all_instances(self) -> List[ManagedReActInstance]:
        """
        Get all initialized instances

        :return: Instance list
        """
        return list(self._instances.values())

    async def destroy_instance(self, instance_id: str) -> bool:
        """
        Destroy the specified ReAct instance

        :param instance_id: Instance ID
        :return: Whether successful
        """
        try:
            if instance_id not in self._instances:
                return False

            instance = self._instances[instance_id]
            await instance.agent.close()
            del self._instances[instance_id]

            return True

        except Exception as e:
            return False

    async def health_check(self) -> Dict[str, Any]:
        """
        Health check

        :return: Health status information
        """
        return {
            "initialized": self._initialized,
            "total_instances": len(self._instances),
            "instances": {
                inst_id: {
                    "created_at": inst.created_at,
                    "use_count": inst.use_count,
                    "last_used": inst.last_used
                }
                for inst_id, inst in self._instances.items()
            }
        }

    async def close(self) -> None:
        """Close the manager and release all resources"""

        for instance_id in list(self._instances.keys()):
            await self.destroy_instance(instance_id)

        self._initialized = False


# Global singleton
react_manager = ReActManager()
