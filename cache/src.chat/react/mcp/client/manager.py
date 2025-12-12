"""Module definition"""

import asyncio
from typing import Dict, List, Optional
from react.mcp.protocol.schema import Tool, ToolResult
from react.config.mcp import MCPConfig
from .client import MCPClient
from .sse import SSEMCPClient


class MCPClientManager:
    
    def __init__(self, config: 'MCPConfig') -> None:
        self.config = config
        self._clients: Dict[str, MCPClient] = {}
        self._connected = False

    def _create_client(self, server: 'MCPConfig.Server') -> MCPClient:
        """
        

        :param server: 
        :return: MCP
        """
        if server.type in ('sse', 'mcp'):
            return SSEMCPClient(server)
        else:
            return MCPClient(server)

    async def initialize(self) -> None:
        """Module definition"""
        for server in self.config.servers:
            client = self._create_client(server)
            await client.connect()
            self._clients[server.name] = client
        self._connected = True

    async def refresh_tools(self) -> Dict[str, Tool]:
        """
        

        :return: 
        """
        all_tools = {}
        for name, client in self._clients.items():
            try:
                tools = await client.list_tools()
                for tool in tools:
                    all_tools[tool.name] = tool
            except Exception as e:
                pass
        return all_tools

    async def call_tool(self, tool_name: str, arguments: Dict) -> ToolResult:
        """
        

        :param tool_name: 
        :param arguments: 
        :return: 
        """
        for name, client in self._clients.items():
            try:
                result = await client.call_tool(tool_name, arguments)
                if not result.is_error:
                    return result
            except Exception as e:
                pass

        return ToolResult(
            content=[],
            is_error=True,
            error_message=""
        )

    def get_tools(self) -> List[Tool]:
        """
        

        :return: 
        """
        tools = []
        for client in self._clients.values():
            try:
                client_tools = asyncio.create_task(client.list_tools())
            except Exception:
                client_tools = []
        return tools

    def get_client(self, name: str) -> Optional[MCPClient]:
        """
        

        :param name: 
        :return: MCP
        """
        return self._clients.get(name)

    async def close(self) -> None:
        """Module definition"""
        for client in self._clients.values():
            await client.close()
        self._clients.clear()
        self._connected = False
