from typing import Callable
from dataclasses import dataclass, asdict
from mcp.types import ToolAnnotations
from mcp.server.fastmcp import FastMCP


@dataclass
class MCPRouter:
    """
    fn: The function to register as a tool
    name: Optional name for the tool (defaults to function name)
    title: Optional human-readable title for the tool
    description: Optional description of what the tool does
    annotations: Optional ToolAnnotations providing additional tool information
    structured_output: Controls whether the tool's output is structured or unstructured
        - If None, auto-detects based on the function's return type annotation
        - If True, unconditionally creates a structured tool (return type annotation permitting)
        - If False, unconditionally creates an unstructured tool
    """
    fn: Callable
    name: str | None = None
    title: str | None = None
    description: str | None = None
    annotations: ToolAnnotations | None = None
    structured_output: bool | None = None

    def as_dict(self):
        return asdict(self)

    def register(self, mcp: FastMCP):
        mcp.add_tool(**self.as_dict())
