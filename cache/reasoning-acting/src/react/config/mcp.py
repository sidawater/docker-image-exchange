"""Module definition"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict


@dataclass
class MCPConfig:

    @dataclass
    class Server:
        """MCP Server Configuration"""
        name: str
        type: str
        command: Optional[str] = None
        url: Optional[str] = None
        args: List[str] = field(default_factory=list)
        headers: Optional[Dict[str, str]] = None
        auth_token: Optional[str] = None
        timeout: int = 30
        reconnect_attempts: int = 3

    servers: List[Server]
    connection_timeout: int = 30
    reconnect_attempts: int = 3
