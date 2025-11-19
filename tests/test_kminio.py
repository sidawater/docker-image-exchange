"""
Unit tests for core.file.client.kminio module
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from asyncio import coroutine
import asyncio
from core.file.client.kminio import AsyncMinioClient, KMinIOBucket


class TestAsyncMinioClient:
    """Test AsyncMinioClient class"""

    def setup_method(self):
        """Reset any patches before each test"""
        patch.stopall()

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test that AsyncMinioClient initializes properly"""
        with patch('core.file.client.kminio.Minio') as MockMinio:
            mock_minio_instance = Mock()
            MockMinio.return_value = mock_minio_instance

            client = AsyncMinioClient(
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret",
                secure=True,
                region="us-east-1",
                max_workers=5
            )

            MockMinio.assert_called_once_with(
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret",
                secure=True,
                region="us-east-1"
            )

            assert client._executor is not None
            assert client._client == mock_minio_instance

    @pytest.mark.asyncio
    async def test_bucket_exists(self):
        """Test bucket_exists method"""
        with patch('core.file.client.kminio.Minio') as MockMinio:
            mock_minio_instance = Mock()
            mock_minio_instance.bucket_exists.return_value = True
            MockMinio.return_value = mock_minio_instance

            client = AsyncMinioClient(
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret"
            )

            result = await client.bucket_exists("test-bucket")

            assert result is True
            mock_minio_instance.bucket_exists.assert_called_once_with("test-bucket")

    @pytest.mark.asyncio
    async def test_make_bucket(self):
        """Test make_bucket method"""
        with patch('core.file.client.kminio.Minio') as MockMinio:
            mock_minio_instance = Mock()
            MockMinio.return_value = mock_minio_instance

            client = AsyncMinioClient(
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret"
            )

            await client.make_bucket("test-bucket", "us-west-2")

            mock_minio_instance.make_bucket.assert_called_once_with("test-bucket", "us-west-2")

    @pytest.mark.asyncio
    async def test_remove_bucket(self):
        """Test remove_bucket method"""
        with patch('core.file.client.kminio.Minio') as MockMinio:
            mock_minio_instance = Mock()
            MockMinio.return_value = mock_minio_instance

            client = AsyncMinioClient(
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret"
            )

            await client.remove_bucket("test-bucket")

            mock_minio_instance.remove_bucket.assert_called_once_with("test-bucket")

    @pytest.mark.asyncio
    async def test_fput_object(self):
        """Test fput_object method"""
        with patch('core.file.client.kminio.Minio') as MockMinio:
            mock_minio_instance = Mock()
            MockMinio.return_value = mock_minio_instance

            client = AsyncMinioClient(
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret"
            )

            await client.fput_object(
                bucket_name="test-bucket",
                object_name="test-object.txt",
                file_path="/path/to/file.txt",
                content_type="text/plain",
                metadata={"key": "value"}
            )

            mock_minio_instance.fput_object.assert_called_once_with(
                "test-bucket",
                "test-object.txt",
                "/path/to/file.txt",
                content_type="text/plain",
                metadata={"key": "value"}
            )

    @pytest.mark.asyncio
    async def test_fget_object(self):
        """Test fget_object method"""
        with patch('core.file.client.kminio.Minio') as MockMinio:
            mock_minio_instance = Mock()
            MockMinio.return_value = mock_minio_instance

            client = AsyncMinioClient(
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret"
            )

            await client.fget_object(
                bucket_name="test-bucket",
                object_name="test-object.txt",
                file_path="/path/to/download.txt"
            )

            mock_minio_instance.fget_object.assert_called_once_with(
                "test-bucket",
                "test-object.txt",
                "/path/to/download.txt"
            )

    @pytest.mark.asyncio
    async def test_put_object(self):
        """Test put_object method"""
        with patch('core.file.client.kminio.Minio') as MockMinio:
            mock_minio_instance = Mock()
            MockMinio.return_value = mock_minio_instance

            client = AsyncMinioClient(
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret"
            )

            mock_data = MagicMock()
            mock_data.read.return_value = b"test data"

            await client.put_object(
                bucket_name="test-bucket",
                object_name="test-object.txt",
                data=mock_data,
                length=100,
                content_type="text/plain"
            )

            mock_minio_instance.put_object.assert_called_once_with(
                "test-bucket",
                "test-object.txt",
                mock_data,
                100,
                content_type="text/plain"
            )

    @pytest.mark.asyncio
    async def test_get_object(self):
        """Test get_object method"""
        with patch('core.file.client.kminio.Minio') as MockMinio:
            mock_minio_instance = Mock()
            mock_response = Mock()
            mock_minio_instance.get_object.return_value = mock_response
            MockMinio.return_value = mock_minio_instance

            client = AsyncMinioClient(
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret"
            )

            result = await client.get_object("test-bucket", "test-object.txt")

            assert result == mock_response
            mock_minio_instance.get_object.assert_called_once_with(
                "test-bucket",
                "test-object.txt"
            )

    @pytest.mark.asyncio
    async def test_list_objects(self):
        """Test list_objects method"""
        with patch('core.file.client.kminio.Minio') as MockMinio:
            mock_minio_instance = Mock()
            mock_objects = [Mock(), Mock()]
            mock_minio_instance.list_objects.return_value = iter(mock_objects)
            MockMinio.return_value = mock_minio_instance

            client = AsyncMinioClient(
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret"
            )

            result = await client.list_objects("test-bucket", prefix="test-", recursive=True)

            assert len(result) == 2
            mock_minio_instance.list_objects.assert_called_once_with(
                "test-bucket",
                prefix="test-",
                recursive=True
            )

    @pytest.mark.asyncio
    async def test_remove_object(self):
        """Test remove_object method"""
        with patch('core.file.client.kminio.Minio') as MockMinio:
            mock_minio_instance = Mock()
            MockMinio.return_value = mock_minio_instance

            client = AsyncMinioClient(
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret"
            )

            await client.remove_object("test-bucket", "test-object.txt")

            mock_minio_instance.remove_object.assert_called_once_with(
                "test-bucket",
                "test-object.txt"
            )

    @pytest.mark.asyncio
    async def test_presigned_get_object(self):
        """Test presigned_get_object method"""
        with patch('core.file.client.kminio.Minio') as MockMinio:
            mock_minio_instance = Mock()
            mock_url = "https://example.com/presigned-url"
            mock_minio_instance.presigned_get_object.return_value = mock_url
            MockMinio.return_value = mock_minio_instance

            client = AsyncMinioClient(
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret"
            )

            result = await client.presigned_get_object(
                "test-bucket",
                "test-object.txt",
                expires=3600
            )

            assert result == mock_url
            mock_minio_instance.presigned_get_object.assert_called_once_with(
                "test-bucket",
                "test-object.txt",
                3600
            )

    @pytest.mark.asyncio
    async def test_presigned_put_object(self):
        """Test presigned_put_object method"""
        with patch('core.file.client.kminio.Minio') as MockMinio:
            mock_minio_instance = Mock()
            mock_url = "https://example.com/presigned-url"
            mock_minio_instance.presigned_put_object.return_value = mock_url
            MockMinio.return_value = mock_minio_instance

            client = AsyncMinioClient(
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret"
            )

            result = await client.presigned_put_object(
                "test-bucket",
                "test-object.txt",
                expires=3600
            )

            assert result == mock_url
            mock_minio_instance.presigned_put_object.assert_called_once_with(
                "test-bucket",
                "test-object.txt",
                3600
            )

    def test_close(self):
        """Test close method"""
        with patch('core.file.client.kminio.Minio') as MockMinio:
            mock_minio_instance = Mock()
            MockMinio.return_value = mock_minio_instance

            client = AsyncMinioClient(
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret"
            )

            mock_executor = Mock()
            client._executor = mock_executor

            client.close()

            mock_executor.shutdown.assert_called_once_with(wait=True)

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """Test async context manager"""
        with patch('core.file.client.kminio.Minio') as MockMinio:
            mock_minio_instance = Mock()
            MockMinio.return_value = mock_minio_instance

            async with AsyncMinioClient(
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret"
            ) as client:
                assert client is not None

            # After exiting context, executor should be closed
            assert client._executor._shutdown is True


class TestKMinIOBucket:
    """Test KMinIOBucket class"""

    def setup_method(self):
        """Reset any patches before each test"""
        patch.stopall()

    @pytest.mark.asyncio
    async def test_bucket_initialization(self):
        """Test that KMinIOBucket initializes properly"""
        with patch('core.file.client.kminio.Minio') as MockMinio:
            mock_minio_instance = Mock()
            MockMinio.return_value = mock_minio_instance

            bucket = KMinIOBucket(
                default_bucket="my-bucket",
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret"
            )

            assert bucket.default_bucket == "my-bucket"
            MockMinio.assert_called_once_with(
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret",
                secure=False,
                region=None
            )

    @pytest.mark.asyncio
    async def test_bucket_exists_uses_default_bucket(self):
        """Test bucket_exists method uses default bucket"""
        with patch('core.file.client.kminio.Minio') as MockMinio:
            mock_minio_instance = Mock()
            mock_minio_instance.bucket_exists.return_value = True
            MockMinio.return_value = mock_minio_instance

            bucket = KMinIOBucket(
                default_bucket="my-bucket",
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret"
            )

            result = await bucket.bucket_exists()

            assert result is True
            mock_minio_instance.bucket_exists.assert_called_once_with("my-bucket")

    @pytest.mark.asyncio
    async def test_make_bucket_uses_default_bucket(self):
        """Test make_bucket method uses default bucket"""
        with patch('core.file.client.kminio.Minio') as MockMinio:
            mock_minio_instance = Mock()
            MockMinio.return_value = mock_minio_instance

            bucket = KMinIOBucket(
                default_bucket="my-bucket",
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret"
            )

            await bucket.make_bucket("us-west-2")

            mock_minio_instance.make_bucket.assert_called_once_with("my-bucket", "us-west-2")

    @pytest.mark.asyncio
    async def test_remove_bucket_uses_default_bucket(self):
        """Test remove_bucket method uses default bucket"""
        with patch('core.file.client.kminio.Minio') as MockMinio:
            mock_minio_instance = Mock()
            MockMinio.return_value = mock_minio_instance

            bucket = KMinIOBucket(
                default_bucket="my-bucket",
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret"
            )

            await bucket.remove_bucket()

            mock_minio_instance.remove_bucket.assert_called_once_with("my-bucket")

    @pytest.mark.asyncio
    async def test_fput_object_uses_default_bucket(self):
        """Test fput_object method uses default bucket"""
        with patch('core.file.client.kminio.Minio') as MockMinio:
            mock_minio_instance = Mock()
            MockMinio.return_value = mock_minio_instance

            bucket = KMinIOBucket(
                default_bucket="my-bucket",
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret"
            )

            await bucket.fput_object(
                object_name="test-object.txt",
                file_path="/path/to/file.txt"
            )

            mock_minio_instance.fput_object.assert_called_once_with(
                "my-bucket",
                "test-object.txt",
                "/path/to/file.txt",
                content_type=None,
                metadata=None
            )

    @pytest.mark.asyncio
    async def test_fget_object_uses_default_bucket(self):
        """Test fget_object method uses default bucket"""
        with patch('core.file.client.kminio.Minio') as MockMinio:
            mock_minio_instance = Mock()
            MockMinio.return_value = mock_minio_instance

            bucket = KMinIOBucket(
                default_bucket="my-bucket",
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret"
            )

            await bucket.fget_object(
                object_name="test-object.txt",
                file_path="/path/to/download.txt"
            )

            mock_minio_instance.fget_object.assert_called_once_with(
                "my-bucket",
                "test-object.txt",
                "/path/to/download.txt"
            )

    @pytest.mark.asyncio
    async def test_put_object_uses_default_bucket(self):
        """Test put_object method uses default bucket"""
        with patch('core.file.client.kminio.Minio') as MockMinio:
            mock_minio_instance = Mock()
            MockMinio.return_value = mock_minio_instance

            bucket = KMinIOBucket(
                default_bucket="my-bucket",
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret"
            )

            mock_data = MagicMock()
            await bucket.put_object(
                object_name="test-object.txt",
                data=mock_data,
                length=100
            )

            mock_minio_instance.put_object.assert_called_once_with(
                "my-bucket",
                "test-object.txt",
                mock_data,
                100,
                content_type=None,
                metadata=None
            )

    @pytest.mark.asyncio
    async def test_get_object_uses_default_bucket(self):
        """Test get_object method uses default bucket"""
        with patch('core.file.client.kminio.Minio') as MockMinio:
            mock_minio_instance = Mock()
            mock_response = Mock()
            mock_minio_instance.get_object.return_value = mock_response
            MockMinio.return_value = mock_minio_instance

            bucket = KMinIOBucket(
                default_bucket="my-bucket",
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret"
            )

            result = await bucket.get_object("test-object.txt")

            assert result == mock_response
            mock_minio_instance.get_object.assert_called_once_with(
                "my-bucket",
                "test-object.txt"
            )

    @pytest.mark.asyncio
    async def test_list_objects_uses_default_bucket(self):
        """Test list_objects method uses default bucket"""
        with patch('core.file.client.kminio.Minio') as MockMinio:
            mock_minio_instance = Mock()
            mock_objects = [Mock(), Mock()]
            mock_minio_instance.list_objects.return_value = iter(mock_objects)
            MockMinio.return_value = mock_minio_instance

            bucket = KMinIOBucket(
                default_bucket="my-bucket",
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret"
            )

            result = await bucket.list_objects(prefix="test-", recursive=True)

            assert len(result) == 2
            mock_minio_instance.list_objects.assert_called_once_with(
                "my-bucket",
                prefix="test-",
                recursive=True
            )

    @pytest.mark.asyncio
    async def test_remove_object_uses_default_bucket(self):
        """Test remove_object method uses default bucket"""
        with patch('core.file.client.kminio.Minio') as MockMinio:
            mock_minio_instance = Mock()
            MockMinio.return_value = mock_minio_instance

            bucket = KMinIOBucket(
                default_bucket="my-bucket",
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret"
            )

            await bucket.remove_object("test-object.txt")

            mock_minio_instance.remove_object.assert_called_once_with(
                "my-bucket",
                "test-object.txt"
            )

    @pytest.mark.asyncio
    async def test_presigned_get_object_uses_default_bucket(self):
        """Test presigned_get_object method uses default bucket"""
        with patch('core.file.client.kminio.Minio') as MockMinio:
            mock_minio_instance = Mock()
            mock_url = "https://example.com/presigned-url"
            mock_minio_instance.presigned_get_object.return_value = mock_url
            MockMinio.return_value = mock_minio_instance

            bucket = KMinIOBucket(
                default_bucket="my-bucket",
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret"
            )

            result = await bucket.presigned_get_object(
                object_name="test-object.txt",
                expires=3600
            )

            assert result == mock_url
            mock_minio_instance.presigned_get_object.assert_called_once_with(
                "my-bucket",
                "test-object.txt",
                3600
            )

    @pytest.mark.asyncio
    async def test_presigned_put_object_uses_default_bucket(self):
        """Test presigned_put_object method uses default bucket"""
        with patch('core.file.client.kminio.Minio') as MockMinio:
            mock_minio_instance = Mock()
            mock_url = "https://example.com/presigned-url"
            mock_minio_instance.presigned_put_object.return_value = mock_url
            MockMinio.return_value = mock_minio_instance

            bucket = KMinIOBucket(
                default_bucket="my-bucket",
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret"
            )

            result = await bucket.presigned_put_object(
                object_name="test-object.txt",
                expires=3600
            )

            assert result == mock_url
            mock_minio_instance.presigned_put_object.assert_called_once_with(
                "my-bucket",
                "test-object.txt",
                3600
            )
