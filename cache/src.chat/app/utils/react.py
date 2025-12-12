"""
SSE Message Processing Utilities

Provides SSEMessage class for handling SSE streaming responses
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from init.utils.json import DefaultEncoder
from react.model.response import MessageType

logger = logging.getLogger(__name__)


class SSEMessage:
    """SSE message class"""

    def __init__(
        self,
        msg_type: MessageType,
        content: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None
    ):
        """
        Initialize SSE message

        :param msg_type: Message type
        :param content: Message content
        :param data: Message data
        :param timestamp: Timestamp
        """
        self.type = msg_type
        self.content = content
        self.data = data or {}
        self.timestamp = timestamp or datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary format
        :return: Dictionary format message
        """
        return {
            "type": self.type,
            "content": self.content,
            "data": self.data,
            "timestamp": self.timestamp
        }

    def to_sse(self) -> str:
        """
        Convert to SSE format string
        :return: SSE format string
        """
        string = json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            cls=DefaultEncoder,
        )
        return f"data: {string}\n\n"
