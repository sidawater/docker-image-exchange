"""Demo script for MCP Client

This script demonstrates how to initialize and use MCP client
through the MCPClientManager for tool discovery and execution.
"""
import os
import sys

sys.path.insert(0, '/data/home/solgeo/projects/reasoning-acting/src')

import asyncio
from typing import Dict, Any

from react.config.mcp import MCPConfig
from react.mcp.client.manager import MCPClientManager
from react.mcp.tool.registry import ToolRegistry


def create_test_config() -> MCPConfig:
    """Create test MCP configuration"""
    return MCPConfig(
        servers=[
            MCPConfig.Server(
                name="test_server",
                type="sse",
                url="http://localhost:3000",  # Change to your MCP server URL
                timeout=30,
            )
        ],
        connection_timeout=30,
        reconnect_attempts=3,
    )


async def test_mcp_basic() -> None:
    """Test basic MCP functionality"""
    print("\n" + "=" * 70)
    print("TEST 1: Initialize MCP Manager")
    print("=" * 70)

    config = create_test_config()
    manager = MCPClientManager(config)

    print(f"Config: {config.servers[0].name} @ {config.servers[0].url}")

    await manager.initialize()
    print("✓ MCP Manager initialized")

    print("\n" + "=" * 70)
    print("TEST 2: Discover Tools")
    print("=" * 70)

    tools = manager.get_tools()
    print(f"✓ Found {len(tools)} tools:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description[:50]}...")

    if not tools:
        print("⚠ No tools discovered - check if MCP server is running")
        print("  Example: npx @modelcontextprotocol/server-filesystem /tmp")

    print("\n" + "=" * 70)
    print("TEST 3: Tool Registry")
    print("=" * 70)

    registry = manager._tool_registry
    print(f"✓ Registry has {len(registry.get_all_tools())} registered tools")

    if tools:
        first_tool = tools[0]
        server_name = registry.get_server_for_tool(first_tool.name)
        print(f"  Tool '{first_tool.name}' is on server '{server_name}'")

    print("\n" + "=" * 70)
    print("TEST 4: Call Tool")
    print("=" * 70)

    if tools:
        tool = tools[0]
        print(f"Calling tool: {tool.name}")

        # Try to get example arguments from schema
        args = {}
        if tool.input_schema and 'properties' in tool.input_schema:
            props = tool.input_schema['properties']
            for key, prop in props.items():
                if 'default' in prop:
                    args[key] = prop['default']
                elif prop.get('type') == 'string':
                    args[key] = "test"
                elif prop.get('type') == 'number':
                    args[key] = 1

        print(f"Arguments: {args}")

        result = await manager.call_tool(tool.name, args)

        if result.is_error:
            print(f"✗ Tool call failed: {result.error_message}")
        else:
            print(f"✓ Tool call succeeded")
            print(f"  Content type: {type(result.content)}")
            print(f"  Content: {result.content}")
    else:
        print("⚠ Skipping tool call - no tools available")

    await manager.close()
    print("\n✓ Connection closed")


async def test_multiple_servers() -> None:
    """Test with multiple MCP servers"""
    print("\n\n" + "=" * 70)
    print("TEST 5: Multiple Servers")
    print("=" * 70)

    config = MCPConfig(
        servers=[
            MCPConfig.Server(
                name="server1",
                type="sse",
                url="http://localhost:3000",
            ),
            MCPConfig.Server(
                name="server2",
                type="sse",
                url="http://localhost:3001",
            ),
        ],
        connection_timeout=30,
    )

    manager = MCPClientManager(config)
    await manager.initialize()

    tools = manager.get_tools()
    print(f"✓ Total tools from {len(config.servers)} servers: {len(tools)}")

    await manager.close()


async def main() -> None:
    """Main test runner"""
    print("\n" + "=" * 70)
    print("MCP CLIENT TEST SUITE")
    print("=" * 70)
    print("\nBefore running:")
    print("1. Make sure proxy env vars are unset: unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY")
    print("2. Start an MCP server, e.g.:")
    print("   npx @modelcontextprotocol/server-filesystem /tmp")
    print("3. Update the server URL in create_test_config() if needed")
    print("=" * 70)

    await test_mcp_basic()
    await test_multiple_servers()

    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
