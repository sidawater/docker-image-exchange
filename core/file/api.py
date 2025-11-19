"""
DocFile manager

from core.file import DocFile

init
DocFile.init(
    bucket_name="user-docs",
    endpoint="minio.example.com:9000",
    access_key="YOUR_ACCESS_KEY",
    secret_key="YOUR_SECRET_KEY"
)

upload
await DocFile.client().upload_from_path(
    "invoices/2023-11-19.pdf",
    "/tmp/invoice_2023-11-19.pdf"
)

"""
from typing import Optional, Dict
from .client import Client


class DocFile:
    """
    Document file storage manager.

    export api:
        init client
    """

    _bucket_name: Optional[str] = None
    _client_map: Dict[str, Client] = {}
    _client: Optional[Client] = None

    @classmethod
    def init(cls, bucket_name: str, backend: str = 'minio', **kwargs) -> None:
        """
        Initialize the storage client for the given backend.

        Args:
            bucket_name (str): The name of the bucket to use.
            backend (str): The storage backend to use (e.g., 'minio').
            **kwargs: Backend-specific configuration (e.g., endpoint, access_key, etc.).
        """
        cls._bucket_name = bucket_name

        if backend == 'minio':
            cls.init_minio(**kwargs)
        else:
            raise ValueError(f"Unsupported backend: {backend}")

    @classmethod
    def init_minio(
        cls,
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool = False,
        region: Optional[str] = None,
        max_workers: int = 10,
    ) -> 'KMinIOBucket':
        """
        Initialize the MinIO asynchronous client with default bucket.

        Args:
            endpoint (str): Host and port of the MinIO server (e.g., "localhost:9000").
            access_key (str): Access key for authentication.
            secret_key (str): Secret key for authentication.
            secure (bool): Use HTTPS if True, HTTP if False. Default is False.
            region (Optional[str]): AWS region name (ignored by MinIO but required for S3 compatibility).
            max_workers (int): Maximum number of threads in the internal thread pool. Default is 10.

        Returns:
            AsyncMinioClient: Initialized async MinIO client instance.
        """
        from .client.kminio import KMinIOBucket

        client = KMinIOBucket(
            default_bucket=cls._bucket_name,
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            region=region,
            max_workers=max_workers,
        )
        cls._client = client
        cls._client_map['minio'] = client
        return client

    @classmethod
    def client(cls) -> Client:
        """
        Get the currently initialized client instance.

        Raises:
            RuntimeError: If no client has been initialized.

        Returns:
            Client: The active storage client.
        """
        if cls._client is None:
            raise RuntimeError("Storage client not initialized. Call DocFile.init() first.")
        return cls._client

    @classmethod
    def bucket_name(cls) -> str:
        """
        Get the configured bucket name.

        Raises:
            RuntimeError: If bucket name is not set.

        Returns:
            str: The bucket name.
        """
        if cls._bucket_name is None:
            raise RuntimeError("Bucket name not set. Call DocFile.init() first.")
        return cls._bucket_name
