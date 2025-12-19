"""Demo script for MCP Client

This script demonstrates how to initialize and use MCP client
through the MCPClientManager for tool discovery and execution.
"""
import os
import sys

sys.path.insert(0, '/data/home/solgeo/projects/reasoning-acting/src')

import asyncio

from react.config.mcp import MCPConfig
from react.mcp.client.manager import MCPClientManager

ENDPOINT = r"http://10.194.203.138/knowledge/mcp-service/mcp"


async def main() -> None:
    """Main async function to demonstrate MCP client usage"""

    print("\n" + "=" * 70)
    print("MCP CLIENT DEMO")
    print("=" * 70)

    print("\nStep 1: Unset proxy variables")
    print("-" * 70)
    proxy_vars = ['http_proxy', 'https_proxy', 'all_proxy',
                  'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY']
    for var in proxy_vars:
        os.environ.pop(var, None)
    print("✓ All proxy variables unset")

    print("\nStep 2: Create MCP configuration")
    print("-" * 70)
    config = MCPConfig(
        servers=[
            MCPConfig.Server(
                name="knowledge_mcp",
                type="sse",
                url=ENDPOINT,
                timeout=30,
            )
        ],
        connection_timeout=30,
    )
    print(f"✓ Config created for: {ENDPOINT}")

    print("\nStep 3: Initialize MCP Manager")
    print("-" * 70)
    manager = MCPClientManager(config)
    await manager.initialize()
    print("✓ MCP Manager initialized")

    print("\nStep 4: Discover tools")
    print("-" * 70)
    tools = manager.get_tools()
    print(f"✓ Found {len(tools)} tools:")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description[:60]}...")

    print("\nStep 5: Test tool call")
    print("-" * 70)
    if tools:
        first_tool = tools[0]
        print(f"Testing tool: {first_tool.name}")

        args = {}
        if hasattr(first_tool, 'input_schema') and first_tool.input_schema:
            props = first_tool.input_schema.get('properties', {})
            for key, prop in props.items():
                if 'default' in prop:
                    args[key] = prop['default']
                elif prop.get('type') == 'string':
                    args[key] = "test"
                elif prop.get('type') == 'number':
                    args[key] = 1

        print(f"Arguments: {args}")
        result = await manager.call_tool(first_tool.name, args)

        if result.is_error:
            print(f"✗ Error: {result.error_message}")
        else:
            print(f"✓ Success!")
            if result.content:
                print(f"Result: {result.content}")

    await manager.close()
    print("\n✓ Connection closed")

    print("\n" + "=" * 70)
    print("DEMO COMPLETED")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
