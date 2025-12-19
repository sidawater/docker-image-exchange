"""Module definition"""

import asyncio
from typing import Dict, List, Optional
from react.mcp.protocol.schema import Tool, ToolResult
from react.config.mcp import MCPConfig
from .sse import SSEMCPClient
from react.mcp.tool.registry import ToolRegistry


class MCPClientManager:

    def __init__(self, config: 'MCPConfig') -> None:
        self.config = config
        self._clients: Dict[str, SSEMCPClient] = {}
        self._tool_registry = ToolRegistry()
        self._connected = False

    def _create_client(self, server: 'MCPConfig.Server') -> SSEMCPClient:
        """
        Create MCP client for server

        :param server: Server configuration
        :return: MCP client instance
        """
        return SSEMCPClient(server)

    async def initialize(self) -> None:
        """
        Initialize all MCP clients and register their tools
        """
        for server in self.config.servers:
            client = self._create_client(server)
            await client.connect()
            self._clients[server.name] = client

        # Refresh tools after all clients are connected
        await self.refresh_tools()
        self._connected = True

    async def refresh_tools(self) -> Dict[str, Tool]:
        """
        Refresh tools from all connected clients and register them

        :return: Dictionary of all available tools
        """
        all_tools = {}
        for server_name, client in self._clients.items():
            try:
                tools = await client.list_tools()
                for tool in tools:
                    self._tool_registry.register(tool, server_name)
                    all_tools[tool.name] = tool
            except Exception as e:
                # Log error but continue
                pass
        return all_tools

    async def call_tool(self, tool_name: str, arguments: Dict) -> ToolResult:
        """
        Call tool by name, routing to the appropriate server

        :param tool_name: Name of the tool to call
        :param arguments: Tool arguments
        :return: Tool execution result
        """
        # Try to route to the correct server based on tool registry
        server_name = self._tool_registry.get_server_for_tool(tool_name)
        if server_name and server_name in self._clients:
            client = self._clients[server_name]
            return await client.call_tool(tool_name, arguments)

        # Fallback: try all clients if routing fails
        for name, client in self._clients.items():
            try:
                result = await client.call_tool(tool_name, arguments)
                if not result.is_error:
                    return result
            except Exception:
                pass

        return ToolResult(
            content=[],
            is_error=True,
            error_message=f"Tool '{tool_name}' not found or all servers failed"
        )

    def get_tools(self) -> List[Tool]:
        """
        Get all registered tools

        :return: List of all available tools
        """
        return self._tool_registry.get_all_tools()

    def get_client(self, name: str) -> Optional[SSEMCPClient]:
        """
        Get client by server name

        :param name: Server name
        :return: MCP client instance or None
        """
        return self._clients.get(name)

    async def close(self) -> None:
        """
        Close all client connections
        """
        for client in self._clients.values():
            await client.close()
        self._clients.clear()
        self._connected = False
