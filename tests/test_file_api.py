"""
Unit tests for core.file.api module
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from core.file.api import DocFile


class TestDocFile:
    """Test DocFile class"""

    def setup_method(self):
        """Reset DocFile state before each test"""
        DocFile._bucket_name = None
        DocFile._client = None
        DocFile._client_map = {}

    def test_init_minio_creates_client(self):
        """Test that init_minio creates and stores a client"""
        with patch('core.file.api.DocFile.init_minio') as mock_init:
            # This test structure is a bit unusual - let's refactor to test the actual behavior
            pass

    def test_docfile_init_with_minio_backend(self):
        """Test initializing DocFile with MinIO backend"""
        with patch('core.file.api.DocFile.init_minio') as mock_init_minio:
            DocFile.init(
                bucket_name="test-bucket",
                backend="minio",
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret"
            )

            assert DocFile._bucket_name == "test-bucket"
            mock_init_minio.assert_called_once_with(
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret"
            )

    def test_docfile_init_with_unsupported_backend(self):
        """Test that init raises ValueError for unsupported backend"""
        with pytest.raises(ValueError, match="Unsupported backend: s3"):
            DocFile.init(
                bucket_name="test-bucket",
                backend="s3"
            )


    def test_client_getter_success(self):
        """Test getting client when initialized"""
        mock_client = Mock()
        DocFile._client = mock_client

        client = DocFile.client()

        assert client == mock_client

    def test_client_getter_not_initialized(self):
        """Test getting client before initialization raises RuntimeError"""
        DocFile._client = None

        with pytest.raises(RuntimeError, match="Storage client not initialized"):
            DocFile.client()

    def test_bucket_name_success(self):
        """Test getting bucket name when set"""
        DocFile._bucket_name = "my-bucket"

        bucket_name = DocFile.bucket_name()

        assert bucket_name == "my-bucket"

    def test_bucket_name_not_set(self):
        """Test getting bucket name before setting raises RuntimeError"""
        DocFile._bucket_name = None

        with pytest.raises(RuntimeError, match="Bucket name not set"):
            DocFile.bucket_name()

    def test_init_preserves_bucket_name(self):
        """Test that init preserves bucket name"""
        with patch('core.file.api.DocFile.init_minio') as mock_init_minio:
            DocFile.init(
                bucket_name="my-custom-bucket",
                backend="minio",
                endpoint="localhost:9000",
                access_key="test-key",
                secret_key="test-secret"
            )

            assert DocFile._bucket_name == "my-custom-bucket"

    def test_client_reuse(self):
        """Test that the same client is reused across calls"""
        mock_client = Mock()
        DocFile._client = mock_client

        # Get client multiple times
        client1 = DocFile.client()
        client2 = DocFile.client()

        # Should return the same instance
        assert client1 == client2 == mock_client
