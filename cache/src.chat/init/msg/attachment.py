"""
Attachment management module

Provides upload, query, download, and deletion functionality for attachments.
"""

from typing import Optional, Dict, Any
from io import BytesIO


class AttachmentClient:
    """
    Attachment management client

    Provides CRUD operations and download functionality for attachments.
    """

    def __init__(self, http_client):
        """
        Initialize attachment client

        :param http_client: HTTP client instance
        """
        self._http = http_client
        self._base_path = "/knowledge/message-service/attachments"

    def upload(
        self,
        file_data: bytes,
        qa_id: str,
        attach_key: int,
        file_type: str,
        filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload attachment

        :param file_data: File data
        :param qa_id: QA record ID
        :param attach_key: Attachment key
        :param file_type: File type
        :param filename: File name
        :return: Uploaded attachment information
        """
        files = {
            "file": (filename or "file", BytesIO(file_data), file_type)
        }
        data = {
            "qa_id": qa_id,
            "attach_key": attach_key,
            "file_type": file_type
        }
        return self._http.post(
            path=f"{self._base_path}/upload",
            files=files,
            data=data
        )

    def get(self, attachment_id: str) -> Dict[str, Any]:
        """
        Get attachment information

        :param attachment_id: Attachment ID
        :return: Attachment metadata information
        """
        return self._http.get(
            path=f"{self._base_path}/{attachment_id}"
        )

    def get_download_url(
        self,
        attachment_id: str,
        expires_in: int = 3600
    ) -> Dict[str, Any]:
        """
        Get attachment temporary download URL

        :param attachment_id: Attachment ID
        :param expires_in: URL expiration time in seconds, maximum 86400
        :return: Response containing temporary URL
        """
        params = {"expires_in": expires_in}
        return self._http.get(
            path=f"{self._base_path}/{attachment_id}/url",
            params=params
        )

    def download(self, attachment_id: str) -> bytes:
        """
        Download attachment content

        :param attachment_id: Attachment ID
        :return: Binary content of the attachment
        """
        temp_url_info = self.get_download_url(attachment_id)
        temp_url = temp_url_info.get("url")

        if not temp_url:
            raise ValueError("Failed to get temporary download URL")

        response = self._http.get_raw(temp_url)
        return response.content

    def delete(self, attachment_id: str) -> Dict[str, Any]:
        """
        Delete attachment (soft delete)

        :param attachment_id: Attachment ID
        :return: Deletion result
        """
        return self._http.delete(
            path=f"{self._base_path}/{attachment_id}"
        )
