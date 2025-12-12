"""TODO Task Definitions"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TODO:
    """Pending task"""
    id: str
    description: str
    action_type: str  # "mcp_tool" | "llm_call" | "condition"
    tool_name: Optional[str] = None
    params: Dict = field(default_factory=dict)
    expected: Dict = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    dependencies: List[str] = field(default_factory=list)
    fallback: Optional[str] = None
    priority: int = 1  # 1-10, 10 is highest priority

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "description": self.description,
            "action_type": self.action_type,
            "tool_name": self.tool_name,
            "params": self.params,
            "expected": self.expected,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "dependencies": self.dependencies,
            "fallback": self.fallback,
            "priority": self.priority
        }

    def can_retry(self) -> bool:
        """Can retry"""
        return self.retry_count < self.max_retries

    def increment_retry(self):
        """Increment retry count"""
        self.retry_count += 1

    def is_completed(self) -> bool:
        """Is completed (can be overridden by subclass)"""
        return False


class MCPtoolTODO(TODO):
    """MCP tool call task"""

    def __init__(
        self,
        id: str,
        description: str,
        tool_name: str,
        params: Optional[Dict] = None,
        expected: Optional[Dict] = None,
        retry_count: int = 0,
        max_retries: int = 3,
        dependencies: Optional[List[str]] = None,
        fallback: Optional[str] = None,
        priority: int = 1
    ):
        super().__init__(
            id=id,
            description=description,
            action_type="mcp_tool",
            tool_name=tool_name,
            params=params or {},
            expected=expected or {},
            retry_count=retry_count,
            max_retries=max_retries,
            dependencies=dependencies or [],
            fallback=fallback,
            priority=priority
        )


class LLMCallTODO(TODO):
    """LLM call task"""

    def __init__(
        self,
        id: str,
        description: str,
        prompt_template: Optional[str] = None,
        messages: Optional[List[Dict]] = None,
        params: Optional[Dict] = None,
        expected: Optional[Dict] = None,
        retry_count: int = 0,
        max_retries: int = 3,
        dependencies: Optional[List[str]] = None,
        fallback: Optional[str] = None,
        priority: int = 1
    ):
        super().__init__(
            id=id,
            description=description,
            action_type="llm_call",
            tool_name=None,
            params=params or {},
            expected=expected or {},
            retry_count=retry_count,
            max_retries=max_retries,
            dependencies=dependencies or [],
            fallback=fallback,
            priority=priority
        )
        self.prompt_template = prompt_template
        self.messages = messages or []


@dataclass
class ConditionTODO(TODO):
    """Conditional judgment task"""
    condition: str = field(default="")
    true_branch: Optional[str] = None
    false_branch: Optional[str] = None

    def __post_init__(self):
        # Automatically set action_type to condition
        self.action_type = "condition"
        if not self.condition:
            raise ValueError("condition is required")
