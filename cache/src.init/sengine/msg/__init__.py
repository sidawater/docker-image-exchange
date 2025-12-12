"""
Message service client

Provides access interface to the message service API, including session management, QA record management, and attachment management functionality.
"""

from typing import Optional
from .client import MessageClient


class MsgManager:
    """
    Message service client manager
    """

    def __init__(self):
        self._client: Optional[MessageClient] = None

    def init(
        self,
        base_url: str,
        api_token: str,
        timeout: int = 30
    ) -> None:
        """
        Initialize message service client manager

        :param base_url: Service base URL
        :param api_token: API access token
        :param timeout: Request timeout in seconds
        """
        if self._client is not None:
            raise RuntimeError("MsgManager already initialized.")

        self._client = MessageClient(
            base_url=base_url,
            api_token=api_token,
            timeout=timeout
        )

    @property
    def client(self) -> MessageClient:
        """
        Get message service client instance

        :return: MessageClient instance
        :raises RuntimeError: If manager not initialized
        """
        if self._client is None:
            raise RuntimeError("MsgManager not initialized. Call .init() first.")
        return self._client

    def close(self) -> None:
        """Close message service client manager"""
        if self._client is not None:
            self._client.close()
            self._client = None


msg_manager: MsgManager = MsgManager()


def get_msg_manager() -> MsgManager:
    """
    Get global MsgManager instance

    :return: Global MsgManager instance
    """
    return msg_manager


__all__ = [
    "msg_manager",
    "get_msg_manager",
    "MsgManager",
    "MessageClient"
]
