"""
Search route registration
"""

from mcp.types import ToolAnnotations
from app.cmcp.router import MCPRouter
from .tool import search_documents, get_references

router_list = [
    MCPRouter(
        fn=search_documents,
        name="search_documents",
        title="Search operations documentation content",
        description="Search for related operations documentation based on rewritten questions and document lists",
        annotations=ToolAnnotations(
            readOnlyHint=True
        ),
        structured_output=True
    ),
    MCPRouter(
        fn=get_references,
        name="get_references",
        title="Format reference documents",
        description="Format search results into a list of reference documents",
        annotations=ToolAnnotations(
            readOnlyHint=True
        ),
        structured_output=None
    )
]
