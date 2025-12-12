"""
Query rewrite route registration
"""

from mcp.types import ToolAnnotations
from app.cmcp.router import MCPRouter
from .tool import rewrite_query

router_list = [
    MCPRouter(
        fn=rewrite_query,
        name="rewrite_query",
        title="Rewrite user query question",
        description="Rewrite user query question based on document list and history records to make it more suitable for document retrieval",
        annotations=ToolAnnotations(
            readOnlyHint=True,
        ),
        structured_output=True,
    )
]
