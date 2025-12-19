"""Module definition"""

from dataclasses import dataclass, field
from typing import Optional

from react.config.mcp import MCPConfig
from react.config.react import ReActConfig


@dataclass
class Settings:
    """Settings for ReAct Agent"""

    llm_config: 'LLMConfig'
    mcp_config: MCPConfig
    react_config: Optional[ReActConfig] = field(default_factory=ReActConfig)

    def validate(self) -> bool:
        """Validate configuration"""
        return True
