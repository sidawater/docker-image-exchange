"""Module definition"""

import json
from typing import Dict, List, Optional, Any
import logging
import traceback
from .client import MCPClient

try:
    import httpx
except ImportError:
    raise RuntimeError(
            "can not find httpx package, pip install httpx\n"
            "or alteretive options: pip install your-package[http]"
        )

from react.mcp.protocol.schema import Tool, ToolResult
from react.config.mcp import MCPConfig

logger = logging.getLogger(__name__)


class SSEMCPClient(MCPClient):

    def __init__(self, config: 'MCPConfig.Server') -> None:
        """
         SSE MCP 

        :param config: MCP
        """
        self.config: MCPConfig.Server = config
        self._connected = False
        self._client: Optional[httpx.AsyncClient] = None
        self._request_id = 0
        self._headers: Dict[str, str] = {}
        self._session_id: Optional[str] = None

    async def connect(self) -> bool:
        """
        :return: 
        """
        try:
            self._headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "Cache-Control": "no-cache"
            }

            if self.config.auth_token:
                self._headers["Authorization"] = f"Bearer {self.config.auth_token}"

            if self.config.headers:
                self._headers.update(self.config.headers)

            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.timeout),
                headers=self._headers
            )

            init_success = await self._initialize_mcp()
            if not init_success:
                self._connected = False
                return False

            self._connected = True
            return True

        except Exception as e:
            logger.error(f'mcp server connect error: {e} {traceback.format_exc()}')
            self._connected = False
            return False
    
    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise ConnectionError('should connect to mcp server first!'
                                  'excute SSEMCPClient.connect')
        
        return self._client
        

    async def _initialize_mcp(self) -> bool:
        """
         MCP 
        :return: 
        """
        try:
            initialize_request = {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "react-agent",
                        "version": "1.0.0"
                    }
                }
            }
            url: str = self.config.url or ''

            response = await self.client.post(url, json=initialize_request)

            if response.status_code != 200:
                return False

            init_result = response.json()
            if "error" in init_result:
                return False

            self._session_id = response.headers.get("mcp-session-id")
            if not self._session_id:
                return False

            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }

            # initializedsession-id
            headers_with_session = dict(self._headers)
            headers_with_session["mcp-session-id"] = self._session_id

            response = await self.client.post(
                url=url,
                json=initialized_notification,
                headers=headers_with_session
            )

            return True

        except Exception as e:
            logger.error(f'mcp server initialized error: {e} {traceback.format_exc()}')
            return False

    def _build_request(self, method: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        JSON-RPC

        :param method: 
        :param params: 
        :return: 
        """
        self._request_id += 1

        request_data = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method
        }

        if params is not None:
            request_data["params"] = params

        return request_data

    async def _send_request(self, method: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        JSON-RPC

        :param method: 
        :param params: 
        :return: 
        """
        if not self._client:
            raise RuntimeError("")

        request_data = self._build_request(method, params)
        request_id = request_data["id"]

        headers = dict(self._headers)
        if self._session_id:
            headers["mcp-session-id"] = self._session_id
        
        url: str = self.config.url or ''

        try:
            response = await self._client.post(
                url=url,
                json=request_data,
                headers=headers
            )
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")

            if "text/event-stream" in content_type:
                result = await self._parse_sse_response(response.text, request_id)
                return result
            else:
                json_result = response.json()
                return json_result

        except httpx.HTTPStatusError as e:
            return {"error": {"code": e.response.status_code, "message": str(e)}}
        except Exception as e:
            logger.error(f'mcp server send request error: {e} {traceback.format_exc()}')
            return {"error": {"code": -1, "message": str(e)}}

    async def _parse_sse_response(self, text: str, request_id: int) -> Dict[str, Any]:
        """
        SSE

        :param text: 
        :param request_id: ID
        :return: 
        """
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue

            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    break

                try:
                    event_data = json.loads(data)
                    if event_data.get("id") == request_id:
                        return event_data
                except json.JSONDecodeError:
                    continue

        return {"error": {"code": -1, "message": ""}}

    async def list_tools(self) -> List[Tool]:
        """
        

        :return: 
        """
        if not self._connected:
            if not await self.connect():
                return []

        try:
            response = await self._send_request("tools/list")  # params
            if "error" in response:
                return []

            tools_data = response.get('result', {}).get("tools", [])
            tools = []

            for tool_data in tools_data:
                tool = Tool(
                    name=tool_data["name"],
                    description=tool_data.get("description", ""),
                    input_schema=tool_data.get("inputSchema", {})
                )
                tools.append(tool)

            return tools

        except Exception as e:
            logger.error(f'mcp list tool error: {e} {traceback.format_exc()}')
            return []

    async def call_tool(self, tool_name: str, arguments: Dict) -> ToolResult:
        """
        

        :param tool_name: 
        :param arguments: 
        :return: 
        """
        if not self._connected:
            if not await self.connect():
                return ToolResult(
                    content=[],
                    is_error=True,
                    error_message=""
                )

        try:
            response = await self._send_request(
                "tools/call",
                {
                    "name": tool_name,
                    "arguments": arguments
                }
            )

            if "error" in response:
                error_msg = response["error"].get("message", "")
                return ToolResult(
                    content=[],
                    is_error=True,
                    error_message=error_msg
                )

            if "result" not in response:
                return ToolResult(
                    content=[],
                    is_error=True,
                    error_message="result"
                )

            result_data = response["result"]
            content = result_data.get("content", [])

            if isinstance(content, str):
                content = [{"type": "text", "text": content}]

            return ToolResult(
                content=content,
                is_error=result_data.get("isError", False)
            )

        except Exception as e:
            logger.error(f'mcp call tool error: {e} {traceback.format_exc()}')

            return ToolResult(
                content=[],
                is_error=True,
                error_message=str(e)
            )

    async def close(self) -> None:
        """Module definition"""
        try:
            if self._client:
                await self._client.aclose()
                self._client = None

            self._connected = False

        except Exception as e:
            logger.error(f'mcp close error: {e} {traceback.format_exc()}')
            pass
