# async_minio_wrapper.py
"""
Asynchronous MinIO Client Wrapper using official `minio` SDK with asyncio compatibility.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, BinaryIO, Dict
from minio import Minio
from minio.datatypes import Object
from minio.error import S3Error


class AsyncMinioClient:
    """
    An asynchronous-compatible wrapper around the official MinIO client.

    This class uses a ThreadPoolExecutor to run blocking MinIO operations in background threads,
    preventing them from blocking the asyncio event loop. It exposes common MinIO operations
    as async methods.

    Initialize the asynchronous MinIO client.

        Args:
            endpoint (str): Host and port of the MinIO server (e.g., "localhost:9000").
            access_key (str): Access key for authentication.
            secret_key (str): Secret key for authentication.
            secure (bool): Use HTTPS if True, HTTP if False. Default is True.
            region (Optional[str]): AWS region name (ignored by MinIO but required for S3 compatibility).
            max_workers (int): Maximum number of threads in the internal thread pool. Default is 10.
        
    """

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool = False,
        region: Optional[str] = None,
        max_workers: int = 3,
    ) -> None:
        self._client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            region=region,
        )
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    async def _run(self, func, *args, **kwargs):
        """
        Helper method to run a synchronous function in the thread pool.

        Args:
            func: The synchronous function to execute.
            *args, **kwargs: Arguments passed to the function.

        Returns:
            The return value of the function.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, lambda: func(*args, **kwargs))

    async def bucket_exists(self, bucket_name: str) -> bool:
        """Check if a bucket exists."""
        return await self._run(self._client.bucket_exists, bucket_name)

    async def make_bucket(self, bucket_name: str, location: Optional[str] = None) -> None:
        """Create a new bucket."""
        await self._run(self._client.make_bucket, bucket_name, location)

    async def remove_bucket(self, bucket_name: str) -> None:
        """Delete an empty bucket."""
        await self._run(self._client.remove_bucket, bucket_name)

    async def fput_object(
        self,
        bucket_name: str,
        object_name: str,
        file_path: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Upload a file from the local filesystem to MinIO.

        Args:
            bucket_name (str): Name of the bucket.
            object_name (str): Object name in the bucket.
            file_path (str): Path to the local file.
            content_type (Optional[str]): MIME type of the object.
            metadata (Optional[Dict[str, str]]): Custom metadata for the object.
        """
        await self._run(
            self._client.fput_object,
            bucket_name,
            object_name,
            file_path,
            content_type=content_type,
            metadata=metadata,
        )

    async def fget_object(
        self,
        bucket_name: str,
        object_name: str,
        file_path: str,
    ) -> None:
        """
        Download an object from MinIO and save it to a local file.

        Args:
            bucket_name (str): Name of the bucket.
            object_name (str): Object name to download.
            file_path (str): Local path to save the file.
        """
        await self._run(
            self._client.fget_object,
            bucket_name,
            object_name,
            file_path,
        )

    async def put_object(
        self,
        bucket_name: str,
        object_name: str,
        data: BinaryIO,
        length: int,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Upload data from a binary stream (e.g., BytesIO) to MinIO.

        Note: The `data` stream must support `.read()` and be seekable or fully loaded in memory.

        Args:
            bucket_name (str): Name of the bucket.
            object_name (str): Object name in the bucket.
            data (BinaryIO): Binary stream containing the data.
            length (int): Total size of the data in bytes.
            content_type (Optional[str]): MIME type.
            metadata (Optional[Dict[str, str]]): Custom metadata.
        """
        await self._run(
            self._client.put_object,
            bucket_name,
            object_name,
            data,
            length,
            content_type=content_type,
            metadata=metadata,
        )

    async def get_object(self, bucket_name: str, object_name: str):
        """
        Retrieve an object from MinIO as a response stream.

        Warning: The returned response object must be explicitly closed by the caller
        to release the underlying HTTP connection.

        Example:
            resp = await client.get_object("my-bucket", "my-file.txt")
            try:
                data = resp.read()
            finally:
                resp.close()
                resp.release_conn()

        Returns:
            A urllib3.HTTPResponse-like object.
        """
        return await self._run(self._client.get_object, bucket_name, object_name)

    async def list_objects(
        self,
        bucket_name: str,
        prefix: str = "",
        recursive: bool = False,
    ) -> List[Object]:
        """
        List objects in a bucket.

        Because the original MinIO client returns an iterator that is not thread-safe across
        executor boundaries, this method consumes the entire iterator in the worker thread
        and returns a list of `Object` instances.

        Args:
            bucket_name (str): Name of the bucket.
            prefix (str): Filter objects by prefix.
            recursive (bool): If True, list objects recursively (ignore directory structure).

        Returns:
            List[Object]: A list of object metadata entries.
        """
        def _list_and_collect():
            # Consume the iterator entirely in the worker thread
            return list(self._client.list_objects(bucket_name, prefix=prefix, recursive=recursive))
        return await self._run(_list_and_collect)

    async def remove_object(self, bucket_name: str, object_name: str) -> None:
        """Delete an object from a bucket."""
        await self._run(self._client.remove_object, bucket_name, object_name)

    async def presigned_get_object(
        self,
        bucket_name: str,
        object_name: str,
        expires: int = 3600,
    ) -> str:
        """
        Generate a presigned URL for downloading an object.

        Args:
            bucket_name (str): Name of the bucket.
            object_name (str): Object name.
            expires (int): Expiration time in seconds (default: 3600 = 1 hour).

        Returns:
            str: A presigned HTTP GET URL.
        """
        return await self._run(
            self._client.presigned_get_object,
            bucket_name,
            object_name,
            expires=expires,
        )

    async def presigned_put_object(
        self,
        bucket_name: str,
        object_name: str,
        expires: int = 3600,
    ) -> str:
        """
        Generate a presigned URL for uploading an object.

        Args:
            bucket_name (str): Name of the bucket.
            object_name (str): Object name.
            expires (int): Expiration time in seconds (default: 3600).

        Returns:
            str: A presigned HTTP PUT URL.
        """
        return await self._run(
            self._client.presigned_put_object,
            bucket_name,
            object_name,
            expires=expires,
        )

    def close(self) -> None:
        """
        Shut down the internal thread pool.

        This should be called when the client is no longer needed.
        Alternatively, use the client as an async context manager (`async with ...`).
        """
        self._executor.shutdown(wait=True)

    async def __aenter__(self):
        """Support for async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Ensure clean shutdown of resources."""
        self.close()


class KMinIOBucket(AsyncMinioClient):
    """
    An extension of AsyncMinioClient that uses a default bucket for all operations.
    """

    def __init__(self, default_bucket: str, *args, **kwargs):
        self.default_bucket = default_bucket
        super().__init__(*args, **kwargs)

    async def bucket_exists(self) -> bool:
        """Check if the default bucket exists."""
        return await super().bucket_exists(self.default_bucket)

    async def make_bucket(self, location: Optional[str] = None) -> None:
        """Create the default bucket."""
        await super().make_bucket(self.default_bucket, location)

    async def remove_bucket(self) -> None:
        """Delete the default bucket (must be empty)."""
        await super().remove_bucket(self.default_bucket)

    async def fput_object(
        self,
        object_name: str,
        file_path: str,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Upload a file from the local filesystem to the default bucket.
        """
        await super().fput_object(
            self.default_bucket,
            object_name,
            file_path,
            content_type=content_type,
            metadata=metadata,
        )

    async def fget_object(
        self,
        object_name: str,
        file_path: str,
    ) -> None:
        """
        Download an object from the default bucket and save it locally.
        """
        await super().fget_object(
            self.default_bucket,
            object_name,
            file_path,
        )

    async def put_object(
        self,
        object_name: str,
        data: BinaryIO,
        length: int,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Upload data from a binary stream to the default bucket.
        """
        await super().put_object(
            self.default_bucket,
            object_name,
            data,
            length,
            content_type=content_type,
            metadata=metadata,
        )

    async def get_object(self, object_name: str):
        """
        Retrieve an object from the default bucket as a response stream.
        """
        return await super().get_object(self.default_bucket, object_name)

    async def list_objects(
        self,
        prefix: str = "",
        recursive: bool = False,
    ) -> List[Object]:
        """
        List objects in the default bucket.
        """
        return await super().list_objects(
            self.default_bucket,
            prefix=prefix,
            recursive=recursive,
        )

    async def remove_object(self, object_name: str) -> None:
        """Delete an object from the default bucket."""
        await super().remove_object(self.default_bucket, object_name)

    async def presigned_get_object(
        self,
        object_name: str,
        expires: int = 3600,
    ) -> str:
        """
        Generate a presigned URL for downloading an object from the default bucket.
        """
        return await super().presigned_get_object(
            self.default_bucket,
            object_name,
            expires=expires,
        )

    async def presigned_put_object(
        self,
        object_name: str,
        expires: int = 3600,
    ) -> str:
        """
        Generate a presigned URL for uploading an object to the default bucket.
        """
        return await super().presigned_put_object(
            self.default_bucket,
            object_name,
            expires=expires,
        )
