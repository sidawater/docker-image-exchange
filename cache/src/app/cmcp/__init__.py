from mcp.server.fastmcp import FastMCP
from typing import Any

def create_mcp():
    mcp = FastMCP(
        "document assistant",
        json_response=True,
    )
    # Set streamable_http_path to "/" to avoid path nesting issues when mounted
    mcp.settings.streamable_http_path = "/"
    # Initialize session manager to avoid "Task group is not initialized" error
    _ = mcp.streamable_http_app()
    return mcp


mcp = create_mcp()


def setup_tools():
    """
    Import tools router and register to mcp
    """
    from app.docrec.router import router_list as docrec_router_list
    from app.intent.router import router_list as intent_router_list
    from app.query.router import router_list as query_router_list
    from app.search.router import router_list as search_router_list

    for router in docrec_router_list:
        router.register(mcp)

    for router in intent_router_list:
        router.register(mcp)

    for router in query_router_list:
        router.register(mcp)

    for router in search_router_list:
        router.register(mcp)
