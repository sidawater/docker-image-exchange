"""
Intent recognition route registration
"""

from mcp.types import ToolAnnotations
from app.cmcp.router import MCPRouter
from .tool import get_intent

router_list = [
    MCPRouter(
        fn=get_intent,
        name="get_intent",
        title="Get user intent classification",
        description="Analyze user queries to determine whether they belong to general conversation or IT operations related issues",
        annotations=ToolAnnotations(
            readOnlyHint=True
        ),
        structured_output=True
    )
]
