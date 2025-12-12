"""
ReAct框架配置

提供ReAct框架的配置管理，包括LLM、MCP等配置。
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from .container import Attr, EnvLoadable
from .base import PartMixin, DictMixin


@dataclass
class MCPConfigItem(EnvLoadable, DictMixin):
    """
    MCP服务器配置项
    """
    name: str = Attr(default='', env="MCP_SERVER_NAME")
    type: str = Attr(default='stdio', env="MCP_SERVER_TYPE")
    command: str = Attr(default='python', env="MCP_SERVER_COMMAND")
    args: str = Attr(default='', env="MCP_SERVER_ARGS")
    env: Optional[Dict[str, str]] = Attr(default=None, env="MCP_SERVER_ENV")


@dataclass
class ReActLLMConfig(EnvLoadable, DictMixin):
    """
    ReAct LLM配置
    """
    provider: str = Attr(default=None, env="REACT_LLM_PROVIDER")
    model: str = Attr(default=None, env="REACT_LLM_MODEL")
    api_key: str = Attr(default=None, env="REACT_LLM_API_KEY")
    base_url: Optional[str] = Attr(default=None, env="REACT_LLM_BASE_URL")
    temperature: float = Attr(default=None, env="REACT_LLM_TEMPERATURE")
    max_tokens: int = Attr(default=None, env="REACT_LLM_MAX_TOKENS")
    timeout: int = Attr(default=None, env="REACT_LLM_TIMEOUT")
    max_retries: int = Attr(default=None, env="REACT_LLM_MAX_RETRIES")


@dataclass
class ReActMCPConfig(EnvLoadable, DictMixin):
    """
    ReAct MCP配置
    """
    enabled: bool = Attr(default=None, env="REACT_MCP_ENABLED")
    servers: Optional[List[MCPConfigItem]] = Attr(
        default=None,
        env="REACT_MCP_SERVERS"
    )


@dataclass
class ReActRAGConfig(EnvLoadable, DictMixin):
    """
    ReAct RAG配置
    """
    enabled: bool = Attr(default=None, env="REACT_RAG_ENABLED")
    endpoint: str = Attr(
        default=None,
        env="REACT_RAG_ENDPOINT"
    )
    api_key: str = Attr(default=None, env="REACT_RAG_API_KEY")
    top_k: int = Attr(default=None, env="REACT_RAG_TOP_K")
    score_threshold: float = Attr(
        default=None,
        env="REACT_RAG_SCORE_THRESHOLD"
    )


@dataclass
class ReActConfig(EnvLoadable, PartMixin, DictMixin):
    """
    ReAct框架主配置
    """
    _prefix: str = "react_"

    llm: ReActLLMConfig = field(default_factory=ReActLLMConfig)
    mcp: ReActMCPConfig = field(default_factory=ReActMCPConfig)
    rag: ReActRAGConfig = field(default_factory=ReActRAGConfig)

    enabled: bool = Attr(default=None, env="REACT_ENABLED")
    max_iterations: int = Attr(default=None, env="REACT_MAX_ITERATIONS")
    timeout: int = Attr(default=None, env="REACT_TIMEOUT")
    enable_streaming: bool = Attr(
        default=None,
        env="REACT_ENABLE_STREAMING"
    )
    stream_chunk_size: int = Attr(
        default=None,
        env="REACT_STREAM_CHUNK_SIZE"
    )


def init_react_config():
    """
    初始化ReAct配置

    :return: ReActConfig实例
    """
    react_config = ReActConfig.load_from_env()
    return react_config
