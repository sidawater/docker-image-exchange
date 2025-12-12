"""Tool Executor"""

import time
from typing import Dict
from react.model.tool import ToolExecutionResult
from react.mcp.protocol.schema import ToolResult


class ToolExecutor:
    """Tool executor"""

    def __init__(self, mcp_manager) -> None:
        self.mcp_manager = mcp_manager

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict,
        timeout: int = 30
    ) -> ToolExecutionResult:
        """Execute tool"""
        start_time = time.time()
        try:
            result = await self.mcp_manager.call_tool(tool_name, arguments)
            duration = time.time() - start_time
            return ToolExecutionResult(
                result=result,
                duration=duration,
                success=True
            )
        except Exception as e:
            duration = time.time() - start_time
            error_result = ToolResult(
                content=[],
                is_error=True,
                error_message=str(e)
            )
            return ToolExecutionResult(
                result=error_result,
                duration=duration,
                success=False
            )
