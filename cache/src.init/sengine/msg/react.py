"""
ReAct instance management module

Provides CRUD operations for ReAct instances
"""

from typing import Optional, Dict, Any, List
from .models import (
    ReActCreateRequest,
    ReActUpdateRequest,
    ReActConfigUpdateRequest,
    ReActStatusUpdateRequest
)


class ReActClient:
    """
    ReAct instance management client

    Provides CRUD operations for ReAct instances
    """

    def __init__(self, http_client):
        """
        Initialize ReAct client

        :param http_client: HTTP client instance
        """
        self._http = http_client
        self._base_path = "/knowledge/message-service/react"

    def create(self, request: ReActCreateRequest) -> Dict[str, Any]:
        """
        Create ReAct instance

        :param request: Creation request
        :return: Created instance information
        """
        return self._http.post(
            path=self._base_path,
            json_data=request.as_dict()
        )

    def get(self, instance_id: str) -> Dict[str, Any]:
        """
        Get ReAct instance details

        :param instance_id: Instance ID
        :return: Instance detailed information
        """
        return self._http.get(
            path=f"{self._base_path}/{instance_id}"
        )

    def list(
        self,
        offset: int = 0,
        limit: int = 20,
        status: Optional[str] = None,
        is_enabled: Optional[bool] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get ReAct instance list

        :param offset: Offset, starting from 0
        :param limit: Page size, maximum 100
        :param status: Status filter
        :param is_enabled: Enable filter
        :param search: Search keywords (search name and code)
        :return: Instance list
        """
        params = {
            "offset": offset,
            "limit": limit
        }
        if status is not None:
            params["status"] = status
        if is_enabled is not None:
            params["is_enabled"] = is_enabled
        if search:
            params["search"] = search

        return self._http.get(
            path=self._base_path,
            params=params
        )

    def update(
        self,
        instance_id: str,
        request: ReActUpdateRequest
    ) -> Dict[str, Any]:
        """
        Update ReAct instance

        :param instance_id: Instance ID
        :param request: Update request
        :return: Updated instance information
        """
        return self._http.put(
            path=f"{self._base_path}/{instance_id}",
            json_data=request.as_dict()
        )

    def delete(self, instance_id: str) -> Dict[str, Any]:
        """
        Delete ReAct instance (soft delete)

        :param instance_id: Instance ID
        :return: Deletion result
        """
        return self._http.delete(
            path=f"{self._base_path}/{instance_id}"
        )

    def update_config(
        self,
        instance_id: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update ReAct configuration

        :param instance_id: Instance ID
        :param config: Configuration dictionary
        :return: Updated instance information
        """
        request = ReActConfigUpdateRequest(config=config)
        return self._http.put(
            path=f"{self._base_path}/{instance_id}/config",
            json_data=request.as_dict()
        )

    def update_status(
        self,
        instance_id: str,
        status: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update ReAct status

        :param instance_id: Instance ID
        :param status: Status
        :param reason: Status change reason
        :return: Updated instance information
        """
        request = ReActStatusUpdateRequest(status=status, reason=reason)
        return self._http.put(
            path=f"{self._base_path}/{instance_id}/status",
            json_data=request.as_dict()
        )

    def get_config(self, instance_id: str) -> Dict[str, Any]:
        """
        Get ReAct configuration

        :param instance_id: Instance ID
        :return: Configuration information
        """
        return self._http.get(
            path=f"{self._base_path}/{instance_id}/config"
        )

    def get_active_instances(self) -> Dict[str, Any]:
        """
        Get all active instances

        :return: Active instance list
        """
        return self.list(
            status="active",
            is_enabled=True,
            offset=0,
            limit=1000
        )

    def test_connection(self, instance_id: str) -> Dict[str, Any]:
        """
        Test ReAct instance connection

        :param instance_id: Instance ID
        :return: Test result
        """
        return self._http.post(
            path=f"{self._base_path}/{instance_id}/test"
        )

    def clone(
        self,
        instance_id: str,
        new_name: str,
        new_code: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Clone ReAct instance

        :param instance_id: Source instance ID
        :param new_name: New instance name
        :param new_code: New instance code
        :param description: New instance description
        :return: Cloned instance information
        """
        return self._http.post(
            path=f"{self._base_path}/{instance_id}/clone",
            json_data={
                "name": new_name,
                "code": new_code,
                "description": description
            }
        )
