"""
Message service client main class

Provides a unified client interface, integrating session, QA, and attachment management functionality.
"""

from typing import Optional, Dict, Any
from .http import HttpClient
from .session import SessionClient
from .qa import QaClient
from .attachment import AttachmentClient
from .react import ReActClient


class MessageClient:
    """
    Message service client

    Unified message service API access interface.
    """

    def __init__(
        self,
        base_url: str,
        api_token: str,
        timeout: int = 30
    ):
        """
        Initialize message service client

        :param base_url: Service base URL, e.g.: http://localhost:8000
        :param api_token: API access token
        :param timeout: Request timeout in seconds, default 30 seconds
        """
        self._http = HttpClient(
            base_url=base_url,
            api_token=api_token,
            timeout=timeout
        )

        self._sessions = SessionClient(self._http)
        self._qa = QaClient(self._http)
        self._attachments = AttachmentClient(self._http)
        self._react = ReActClient(self._http)

    @property
    def sessions(self) -> SessionClient:
        """
        Get session management client

        :return: Session client instance
        """
        return self._sessions

    @property
    def qa(self) -> QaClient:
        """
        Get QA record management client

        :return: QA client instance
        """
        return self._qa

    @property
    def attachments(self) -> AttachmentClient:
        """
        Get attachment management client

        :return: Attachment client instance
        """
        return self._attachments

    @property
    def react(self) -> ReActClient:
        """
        Get ReAct instance management client

        :return: ReAct client instance
        """
        return self._react

    def health_check(self) -> Dict[str, Any]:
        """
        Health check

        :return: Service status information
        """
        return self._http.get("")

    def get_swagger_docs(self) -> Dict[str, Any]:
        """
        Get Swagger API documentation

        :return: API documentation information
        """
        return self._http.get("/knowledge/message-service/docs")

    def close(self):
        """Close client"""
        self._http.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
