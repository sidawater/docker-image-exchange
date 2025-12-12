"""
QA record management module

Provides creation, query, update, and search functionality for QA records.
"""

from typing import Optional, Dict, Any, List
from .models import (
    QaCreateRequest,
    QaUpdateRequest,
    QaSearchParams
)


class QaClient:
    """
    QA record management client

    Provides CRUD operations and search functionality for QA records.
    """

    def __init__(self, http_client):
        """
        Initialize QA client

        :param http_client: HTTP client instance
        """
        self._http = http_client
        self._base_path = "/messages/qa"

    def create(self, request: QaCreateRequest) -> Dict[str, Any]:
        """
        Create QA record

        :param request: QA creation request
        :return: Created QA record information
        """
        return self._http.post(
            path=self._base_path,
            json_data=request.as_dict()
        )

    def get(self, qa_id: str) -> Dict[str, Any]:
        """
        Get QA record details

        :param qa_id: QA record ID
        :return: QA record detailed information
        """
        return self._http.get(
            path=f"{self._base_path}/{qa_id}"
        )

    def update(
        self,
        qa_id: str,
        request: QaUpdateRequest
    ) -> Dict[str, Any]:
        """
        Update QA record

        :param qa_id: QA record ID
        :param request: QA update request
        :return: Updated QA record information
        """
        return self._http.put(
            path=f"{self._base_path}/{qa_id}",
            json_data=request.as_dict()
        )

    def search(
        self,
        params: Optional[QaSearchParams] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Search QA records

        :param params: Search parameters
        :param kwargs: Additional search parameters
        :return: QA record list
        """
        if params is None:
            params = QaSearchParams(**kwargs)
        else:
            params_dict = params.as_dict()
            params_dict.update(kwargs)
            params = QaSearchParams(**params_dict)

        return self._http.get(
            path=f"{self._base_path}/search",
            params=params.as_dict()
        )

    def get_by_session(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get all QA records for a session

        :param session_id: Session ID
        :param limit: Return limit, maximum 1000
        :param offset: Offset
        :return: QA record list
        """
        params = {
            "limit": limit,
            "offset": offset
        }
        return self._http.get(
            path=f"{self._base_path}/session/{session_id}",
            params=params
        )
