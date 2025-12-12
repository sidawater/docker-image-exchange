"""Module definition"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Tool:
    name: str
    description: str
    input_schema: Dict


@dataclass
class ToolResult:
    content: List[Dict]
    is_error: bool = False
    error_message: Optional[str] = None


# @dataclass
# class ActionPlan:
#     action: 'Action'
#     reasoning: str
