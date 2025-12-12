"""Module definition"""

from typing import List, Optional, Dict
from react.mcp.protocol.schema import Tool


class ToolRegistry:
    
    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}
        self._tool_to_server: Dict[str, str] = {}

    def register(self, tool: Tool, server_name: str) -> None:
        """Module definition"""
        self._tools[tool.name] = tool
        self._tool_to_server[tool.name] = server_name

    def get_all_tools(self) -> List[Tool]:
        """Module definition"""
        return list(self._tools.values())

    def get_tool(self, name: str) -> Optional[Tool]:
        """Module definition"""
        return self._tools.get(name)

    def get_server_for_tool(self, tool_name: str) -> Optional[str]:
        """Module definition"""
        return self._tool_to_server.get(tool_name)
