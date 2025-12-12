"""Module definition"""

from typing import List
from react.mcp.protocol.schema import Tool
from react.mcp.client.client import MCPClient

class ToolDiscoverer:
    
    def __init__(self, client: 'MCPClient') -> None:
        self.client = client

    async def discover(self) -> List[Tool]:
        """Module definition"""
        return await self.client.list_tools()
