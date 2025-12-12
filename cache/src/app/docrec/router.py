"""
Document recognition route registration
"""

from mcp.types import ToolAnnotations
from app.cmcp.router import MCPRouter
from .tool import recognize_documents

router_list = [
    MCPRouter(
        fn=recognize_documents,
        name="recognize_documents",
        title="Recognize operations document names",
        description="Recognize related operations document name list based on user queries, history records and cache",
        annotations=ToolAnnotations(
            readOnlyHint=True
        ),
        structured_output=True
    )
]
