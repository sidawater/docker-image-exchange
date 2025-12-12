"""
Session management module

Provides session creation, query, update, and deletion functionality.
"""

from typing import Optional, Dict, Any, List
from .models import SessionCreateRequest, SessionUpdateRequest


class SessionClient:
    """
    Session management client

    Provides CRUD operations for sessions.
    """

    def __init__(self, http_client):
        """
        Initialize session client

        :param http_client: HTTP client instance
        """
        self._http = http_client
        self._base_path = "/messages/sessions"

    def create(self, request: SessionCreateRequest) -> Dict[str, Any]:
        """
        Create a session

        :param request: Session creation request
        :return: Created session information
        """
        return self._http.post(
            path=self._base_path,
            json_data=request.as_dict()
        )

    def get(self, session_id: str) -> Dict[str, Any]:
        """
        Get session details

        :param session_id: Session ID
        :return: Session detailed information
        """
        return self._http.get(
            path=f"{self._base_path}/{session_id}"
        )

    def list(
        self,
        user_id: str,
        offset: int = 0,
        limit: int = 20,
        active_only: bool = True
    ) -> Dict[str, Any]:
        """
        Get user session list

        :param user_id: User ID
        :param offset: Offset, starting from 0
        :param limit: Page size, maximum 100
        :param active_only: Whether to return only active sessions
        :return: Session list
        """
        params = {
            "user_id": user_id,
            "offset": offset,
            "limit": limit,
            "active_only": active_only
        }
        return self._http.get(
            path=self._base_path,
            params=params
        )

    def update(
        self,
        session_id: str,
        request: SessionUpdateRequest
    ) -> Dict[str, Any]:
        """
        Update a session

        :param session_id: Session ID
        :param request: Session update request
        :return: Updated session information
        """
        return self._http.put(
            path=f"{self._base_path}/{session_id}",
            json_data=request.as_dict()
        )

    def delete(self, session_id: str) -> Dict[str, Any]:
        """
        Delete a session (soft delete)

        :param session_id: Session ID
        :return: Deletion result
        """
        return self._http.delete(
            path=f"{self._base_path}/{session_id}"
        )
