"""Exception Definitions"""


class AgentException(Exception):
    """Agent exception"""

    pass


class ToolExecutionException(AgentException):
    """Tool execution exception"""

    pass


class ReasoningTimeoutException(AgentException):
    """Reasoning timeout exception"""

    pass


class ConfigurationException(AgentException):
    """Configuration exception"""

    pass


class MCPConnectionException(AgentException):
    """MCP connection exception"""

    pass
