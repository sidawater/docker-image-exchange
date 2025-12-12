"""
HTTP client module

Encapsulates HTTP request logic, providing a unified interface.
"""

import json
from typing import Dict, Any, Optional, Union
import httpx
from .exceptions import (
    ValidationError,
    NotFoundError,
    AuthenticationError,
    ServerError,
    MessageServiceError
)


class HttpClient:
    """
    HTTP client

    Encapsulates HTTP requests, handling responses and exceptions.
    """

    def __init__(
        self,
        base_url: str,
        api_token: str,
        timeout: int = 30
    ):
        """
        Initialize HTTP client

        :param base_url: Service base URL
        :param api_token: API access token
        :param timeout: Request timeout in seconds
        """
        self._base_url = base_url.rstrip("/")
        self._api_token = api_token
        self._timeout = timeout
        self._client = httpx.Client(timeout=timeout)

        self._headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """
        Handle HTTP response

        :param response: HTTP response object
        :return: Parsed response data
        :raises: Corresponding exceptions
        """
        status_code = response.status_code

        if status_code == 200:
            if response.content:
                data = response.json()
                # Extract 'data' field if present (server wraps response in success/data format)
                if isinstance(data, dict) and 'data' in data:
                    return data['data']
                return data
            return {}
        elif status_code == 422:
            error_data = response.json()
            raise ValidationError(
                f"Validation error: {json.dumps(error_data, indent=2)}"
            )
        elif status_code == 401:
            raise AuthenticationError("Authentication failed")
        elif status_code == 404:
            raise NotFoundError("Resource not found")
        elif status_code >= 500:
            raise ServerError(f"Server error: {status_code}")
        else:
            raise MessageServiceError(
                f"Unexpected error: {status_code}, "
                f"response: {response.text}"
            )

    def _make_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request

        :param method: HTTP method
        :param path: Request path
        :param params: URL parameters
        :param json_data: JSON data
        :param files: File data
        :param data: Form data
        :return: Response data
        """
        url = f"{self._base_url}/{path.lstrip('/')}"

        headers = self._headers.copy()
        if files:
            headers.pop("Content-Type", None)

        try:
            response = self._client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data,
                files=files,
                data=data
            )
            return self._handle_response(response)
        except httpx.RequestError as e:
            raise MessageServiceError(f"Request failed: {str(e)}")

    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make GET request

        :param path: Request path
        :param params: URL parameters
        :return: Response data
        """
        return self._make_request("GET", path, params=params)

    def get_raw(self, url: str) -> httpx.Response:
        """
        Make raw GET request (not through base_url)

        :param url: Complete URL
        :return: HTTP response object
        """
        headers = {
            "Authorization": f"Bearer {self._api_token}",
            "Accept": "application/json"
        }
        response = self._client.get(url, headers=headers)
        response.raise_for_status()
        return response

    def post(
        self,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make POST request

        :param path: Request path
        :param json_data: JSON data
        :param files: File data
        :param data: Form data
        :return: Response data
        """
        return self._make_request(
            "POST",
            path,
            json_data=json_data,
            files=files,
            data=data
        )

    def put(
        self,
        path: str,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make PUT request

        :param path: Request path
        :param json_data: JSON data
        :return: Response data
        """
        return self._make_request("PUT", path, json_data=json_data)

    def delete(self, path: str) -> Dict[str, Any]:
        """
        Make DELETE request

        :param path: Request path
        :return: Response data
        """
        return self._make_request("DELETE", path)

    def close(self):
        """Close client"""
        self._client.close()
