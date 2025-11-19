"""
Pytest configuration and shared fixtures
"""
import asyncio
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_dir():
    """Create a temporary directory that is cleaned up after the test"""
    temp_directory = tempfile.mkdtemp()
    yield temp_directory
    shutil.rmtree(temp_directory, ignore_errors=True)


@pytest.fixture
def temp_file():
    """Create a temporary file that is cleaned up after the test"""
    fd, temp_path = tempfile.mkstemp()
    os.close(fd)
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def mock_minio_client():
    """Create a mock MinIO client"""
    return Mock()


@pytest.fixture
def mock_async_minio_client():
    """Create a mock async MinIO client with async methods"""
    client = Mock()
    client.bucket_exists = Mock(return_value=True)
    client.make_bucket = Mock()
    client.remove_bucket = Mock()
    client.fput_object = Mock()
    client.fget_object = Mock()
    client.put_object = Mock()
    client.get_object = Mock()
    client.list_objects = Mock(return_value=[])
    client.remove_object = Mock()
    client.presigned_get_object = Mock(return_value="https://example.com/url")
    client.presigned_put_object = Mock(return_value="https://example.com/url")
    client.close = Mock()
    return client


@pytest.fixture
def sample_knowledge_base(temp_dir):
    """Create a sample knowledge base structure for testing"""
    # Create directory structure
    knowledge_dir = Path(temp_dir) / "knowledge_base"
    knowledge_dir.mkdir()

    # Create files
    (knowledge_dir / "README.md").write_text("# Knowledge Base\n\nThis is a test knowledge base.")
    (knowledge_dir / "index.md").write_text("Index file")

    # Create section1
    section1 = knowledge_dir / "section1"
    section1.mkdir()
    (section1 / "file1.md").write_text("Content 1")
    (section1 / "file2.md").write_text("Content 2")

    # Create subsection
    subsection = section1 / "subsection"
    subsection.mkdir()
    (subsection / "nested_file.md").write_text("Nested content")

    # Create section2
    section2 = knowledge_dir / "section2"
    section2.mkdir()
    (section2 / "another_file.md").write_text("More content")

    return str(knowledge_dir)


@pytest.fixture
def sample_document_metadata():
    """Create a sample DocumentMetadata object"""
    from datetime import datetime
    from core.schema import DocumentMetadata, Tag

    now = datetime.now()
    tags = [
        Tag(name="important", tag_domain="priority", display_name="Important"),
        Tag(name="draft", tag_domain="status", display_name="Draft")
    ]

    return DocumentMetadata(
        name="test.pdf",
        content_type="application/pdf",
        size=1024,
        created_at=now,
        updated_at=now,
        description="Test document",
        tags=tags,
        custom_fields={"author": "Test User"},
        aliases=["doc1", "document_one"]
    )


@pytest.fixture
def sample_document(sample_document_metadata):
    """Create a sample Document object"""
    from core.schema import Document

    return Document(
        key="doc-001",
        metadata=sample_document_metadata,
        storage_key="docs/test.pdf"
    )


@pytest.fixture
def mock_docfile_client():
    """Create a mock DocFile client"""
    mock_client = Mock()
    mock_client.fput_object = Mock()
    mock_client.fget_object = Mock()
    mock_client.list_objects = Mock(return_value=[])
    return mock_client


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )


# Run tests asynchronously
def pytest_collection_modifyitems(config, items):
    """Mark async tests"""
    import inspect
    for item in items:
        if item.function and inspect.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)
