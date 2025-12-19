"""Simple MCP Client Demo with Built-in HTTP Server

This script demonstrates MCP client functionality with a simple HTTP server
that provides test tools. No external dependencies required.
"""
import os
import sys
import json
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from typing import Dict, Any

sys.path.insert(0, '/data/home/solgeo/projects/reasoning-acting/src')

from react.config.mcp import MCPConfig
from react.mcp.client.manager import MCPClientManager


class MCPTestHandler(BaseHTTPRequestHandler):
    """Simple MCP test server handler"""

    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')

        try:
            data = json.loads(body)
            method = data.get('method')

            if method == 'initialize':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('mcp-session-id', 'test-session-123')
                self.end_headers()

                response = {
                    "jsonrpc": "2.0",
                    "id": data.get('id'),
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "serverInfo": {"name": "test-mcp-server", "version": "1.0.0"}
                    }
                }
                self.wfile.write(json.dumps(response).encode())

            elif method == 'notifications/initialized':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"jsonrpc":"2.0"}')

            elif method == 'tools/list':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()

                response = {
                    "jsonrpc": "2.0",
                    "id": data.get('id'),
                    "result": {
                        "tools": [
                            {
                                "name": "echo",
                                "description": "Echo back the input message",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "message": {"type": "string", "description": "Message to echo"}
                                    },
                                    "required": ["message"]
                                }
                            },
                            {
                                "name": "add",
                                "description": "Add two numbers",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "a": {"type": "number", "description": "First number"},
                                        "b": {"type": "number", "description": "Second number"}
                                    },
                                    "required": ["a", "b"]
                                }
                            },
                            {
                                "name": "get_time",
                                "description": "Get current timestamp",
                                "inputSchema": {"type": "object", "properties": {}, "required": []}
                            }
                        ]
                    }
                }
                self.wfile.write(json.dumps(response).encode())

            elif method == 'tools/call':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()

                params = data.get('params', {})
                tool_name = params.get('name')
                arguments = params.get('arguments', {})

                if tool_name == 'echo':
                    message = arguments.get('message', '')
                    result_text = f"Echo: {message}"
                elif tool_name == 'add':
                    a = arguments.get('a', 0)
                    b = arguments.get('b', 0)
                    result_text = f"Result: {a + b}"
                elif tool_name == 'get_time':
                    import time
                    timestamp = int(time.time())
                    result_text = f"Current timestamp: {timestamp}"
                else:
                    self.send_response(400)
                    self.end_headers()
                    error = {"jsonrpc": "2.0", "id": data.get('id'),
                            "error": {"code": -32601, "message": "Tool not found"}}
                    self.wfile.write(json.dumps(error).encode())
                    return

                response = {
                    "jsonrpc": "2.0",
                    "id": data.get('id'),
                    "result": {
                        "content": [{"type": "text", "text": result_text}],
                        "isError": False
                    }
                }
                self.wfile.write(json.dumps(response).encode())

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            error = {"jsonrpc": "2.0", "id": 0,
                    "error": {"code": -32603, "message": str(e)}}
            self.wfile.write(json.dumps(error).encode())

    def log_message(self, format, *args):
        """Suppress server logs"""
        pass


def start_test_server(port: int = 3001) -> HTTPServer:
    """Start test MCP server"""
    server = HTTPServer(('localhost', port), MCPTestHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"✓ Test MCP server started on http://localhost:{port}")
    return server


async def main():
    """Main test"""
    print("\n" + "=" * 70)
    print("MCP CLIENT SIMPLE TEST")
    print("=" * 70)

    # Unset proxy variables
    proxy_vars = ['http_proxy', 'https_proxy', 'all_proxy',
                  'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY']
    for var in proxy_vars:
        os.environ.pop(var, None)

    # Start test server
    print("\nStarting test MCP server...")
    server = start_test_server(3001)
    await asyncio.sleep(0.5)

    try:
        # Create MCP manager
        config = MCPConfig(
            servers=[
                MCPConfig.Server(
                    name="test_server",
                    type="sse",
                    url="http://localhost:3001",
                    timeout=10,
                )
            ]
        )

        print("\n" + "-" * 70)
        print("1. Initializing MCP Manager")
        print("-" * 70)
        manager = MCPClientManager(config)
        await manager.initialize()
        print("✓ Manager initialized")

        # Discover tools
        print("\n" + "-" * 70)
        print("2. Discovering Tools")
        print("-" * 70)
        tools = manager.get_tools()
        print(f"✓ Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")

        # Test tool calls
        print("\n" + "-" * 70)
        print("3. Testing Tool Calls")
        print("-" * 70)

        # Test echo
        print("\nTest: echo tool")
        result = await manager.call_tool("echo", {"message": "Hello MCP!"})
        print(f"Result: {result.content[0]['text']}")

        # Test add
        print("\nTest: add tool")
        result = await manager.call_tool("add", {"a": 5, "b": 3})
        print(f"Result: {result.content[0]['text']}")

        # Test get_time
        print("\nTest: get_time tool")
        result = await manager.call_tool("get_time", {})
        print(f"Result: {result.content[0]['text']}")

        # Test invalid tool
        print("\nTest: invalid tool")
        result = await manager.call_tool("invalid_tool", {})
        print(f"Error: {result.error_message}")

        await manager.close()
        print("\n✓ Connection closed")

    finally:
        server.shutdown()
        print("✓ Test server stopped")

    print("\n" + "=" * 70)
    print("TEST COMPLETED SUCCESSFULLY")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nTest failed: {e}")
        import traceback
        traceback.print_exc()
