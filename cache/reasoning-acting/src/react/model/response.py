"""Response Data Models"""

from dataclasses import dataclass
from typing import Union, Any
from enum import Enum


class MessageType(Enum):
    """Message types for streaming output"""
    THINKING = "thinking"
    CONTENT = "content"
    TOOL_CALL = "tool-call"
    TOOL_RESULT = "tool-result"
    ERROR = "error"
    STATUS = "status"
    METADATA = "metadata"


@dataclass
class ResponseData:
    """Response data structure for streaming output"""
    message_type: MessageType
    data: Union[str, dict, Any]

    def as_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "message_type": self.message_type.value,
            "data": self.data
        }
