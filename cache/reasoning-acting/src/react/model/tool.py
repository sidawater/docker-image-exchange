"""Tool-related Data Models"""

from dataclasses import dataclass, field
from typing import Dict
from datetime import datetime
from react.mcp.protocol.schema import ToolResult


@dataclass
class ToolCall:
    """Tool Call"""
    tool_name: str
    arguments: Dict
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ToolExecutionResult:
    """Tool Execution Result"""
    result: 'ToolResult'
    duration: float
    success: bool
