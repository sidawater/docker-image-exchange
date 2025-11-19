"""
Unit tests for core.schema module
"""
import pytest
from datetime import datetime
from core.schema import Tag, TagDomain, DocumentMetadata, Document


class TestTagDomain:
    """Test TagDomain dataclass"""

    def test_tag_domain_creation(self):
        """Test creating a TagDomain with name only"""
        tag_domain = TagDomain(name="category")
        assert tag_domain.name == "category"
        assert tag_domain.display_name == ""

    def test_tag_domain_with_display_name(self):
        """Test creating a TagDomain with both name and display_name"""
        tag_domain = TagDomain(name="category", display_name="Category")
        assert tag_domain.name == "category"
        assert tag_domain.display_name == "Category"


class TestTag:
    """Test Tag dataclass"""

    def test_tag_creation(self):
        """Test creating a Tag"""
        tag = Tag(
            name="important",
            tag_domain="priority",
            display_name="Important"
        )
        assert tag.name == "important"
        assert tag.tag_domain == "priority"
        assert tag.display_name == "Important"

    def test_tag_to_dict(self):
        """Test converting Tag to dictionary"""
        tag = Tag(
            name="important",
            tag_domain="priority",
            display_name="Important"
        )
        tag_dict = tag.to_dict()
        assert tag_dict == {
            "name": "important",
            "tag_domain": "priority",
            "display_name": "Important"
        }

    def test_tag_from_dict(self):
        """Test creating Tag from dictionary"""
        tag_dict = {
            "name": "important",
            "tag_domain": "priority",
            "display_name": "Important"
        }
        tag = Tag.from_dict(tag_dict)
        assert tag.name == "important"
        assert tag.tag_domain == "priority"
        assert tag.display_name == "Important"

    def test_tag_round_trip(self):
        """Test Tag serialization round trip"""
        original_tag = Tag(
            name="test",
            tag_domain="type",
            display_name="Test Tag"
        )
        tag_dict = original_tag.to_dict()
        restored_tag = Tag.from_dict(tag_dict)

        assert restored_tag.name == original_tag.name
        assert restored_tag.tag_domain == original_tag.tag_domain
        assert restored_tag.display_name == original_tag.display_name


class TestDocumentMetadata:
    """Test DocumentMetadata dataclass"""

    def test_document_metadata_creation(self):
        """Test creating DocumentMetadata with all required fields"""
        now = datetime.now()
        metadata = DocumentMetadata(
            name="test.pdf",
            content_type="application/pdf",
            size=1024,
            created_at=now,
            updated_at=now
        )
        assert metadata.name == "test.pdf"
        assert metadata.content_type == "application/pdf"
        assert metadata.size == 1024
        assert metadata.created_at == now
        assert metadata.updated_at == now
        assert metadata.description is None
        assert metadata.tags == []
        assert metadata.custom_fields is None
        assert metadata.aliases == []

    def test_document_metadata_with_optional_fields(self):
        """Test creating DocumentMetadata with optional fields"""
        now = datetime.now()
        metadata = DocumentMetadata(
            name="test.pdf",
            content_type="application/pdf",
            size=1024,
            created_at=now,
            updated_at=now,
            description="Test document",
            custom_fields={"author": "Test User"},
            aliases=["doc1", "document_one"]
        )
        assert metadata.description == "Test document"
        assert metadata.custom_fields == {"author": "Test User"}
        assert metadata.aliases == ["doc1", "document_one"]

    def test_document_metadata_with_tags(self):
        """Test creating DocumentMetadata with tags"""
        now = datetime.now()
        tags = [
            Tag(name="important", tag_domain="priority", display_name="Important"),
            Tag(name="draft", tag_domain="status", display_name="Draft")
        ]
        metadata = DocumentMetadata(
            name="test.pdf",
            content_type="application/pdf",
            size=1024,
            created_at=now,
            updated_at=now,
            tags=tags
        )
        assert len(metadata.tags) == 2
        assert metadata.tags[0].name == "important"
        assert metadata.tags[1].name == "draft"

    def test_document_metadata_to_dict(self):
        """Test converting DocumentMetadata to dictionary"""
        now = datetime(2024, 1, 1, 12, 0, 0)
        tags = [
            Tag(name="important", tag_domain="priority", display_name="Important")
        ]
        metadata = DocumentMetadata(
            name="test.pdf",
            content_type="application/pdf",
            size=1024,
            created_at=now,
            updated_at=now,
            tags=tags
        )
        metadata_dict = metadata.to_dict()

        assert metadata_dict["name"] == "test.pdf"
        assert metadata_dict["content_type"] == "application/pdf"
        assert metadata_dict["size"] == 1024
        assert metadata_dict["created_at"] == "2024-01-01T12:00:00"
        assert metadata_dict["updated_at"] == "2024-01-01T12:00:00"
        assert len(metadata_dict["tags"]) == 1
        assert metadata_dict["tags"][0]["name"] == "important"

    def test_document_metadata_from_dict(self):
        """Test creating DocumentMetadata from dictionary"""
        metadata_dict = {
            "name": "test.pdf",
            "content_type": "application/pdf",
            "size": 1024,
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00",
            "description": "Test document",
            "tags": [
                {
                    "name": "important",
                    "tag_domain": "priority",
                    "display_name": "Important"
                }
            ],
            "custom_fields": {"author": "Test User"},
            "aliases": ["doc1"]
        }

        metadata = DocumentMetadata.from_dict(metadata_dict)

        assert metadata.name == "test.pdf"
        assert metadata.content_type == "application/pdf"
        assert metadata.size == 1024
        assert metadata.created_at == datetime(2024, 1, 1, 12, 0, 0)
        assert metadata.updated_at == datetime(2024, 1, 1, 12, 0, 0)
        assert metadata.description == "Test document"
        assert len(metadata.tags) == 1
        assert metadata.tags[0].name == "important"
        assert metadata.custom_fields == {"author": "Test User"}
        assert metadata.aliases == ["doc1"]

    def test_document_metadata_round_trip(self):
        """Test DocumentMetadata serialization round trip"""
        now = datetime(2024, 1, 1, 12, 0, 0)
        tags = [
            Tag(name="important", tag_domain="priority", display_name="Important")
        ]
        original_metadata = DocumentMetadata(
            name="test.pdf",
            content_type="application/pdf",
            size=1024,
            created_at=now,
            updated_at=now,
            description="Test document",
            tags=tags,
            custom_fields={"author": "Test User"},
            aliases=["doc1"]
        )

        metadata_dict = original_metadata.to_dict()
        restored_metadata = DocumentMetadata.from_dict(metadata_dict)

        assert restored_metadata.name == original_metadata.name
        assert restored_metadata.content_type == original_metadata.content_type
        assert restored_metadata.size == original_metadata.size
        assert restored_metadata.created_at == original_metadata.created_at
        assert restored_metadata.updated_at == original_metadata.updated_at
        assert restored_metadata.description == original_metadata.description
        assert len(restored_metadata.tags) == len(original_metadata.tags)
        assert restored_metadata.tags[0].name == original_metadata.tags[0].name
        assert restored_metadata.custom_fields == original_metadata.custom_fields
        assert restored_metadata.aliases == original_metadata.aliases


class TestDocument:
    """Test Document dataclass"""

    def test_document_creation(self):
        """Test creating a Document"""
        now = datetime.now()
        metadata = DocumentMetadata(
            name="test.pdf",
            content_type="application/pdf",
            size=1024,
            created_at=now,
            updated_at=now
        )
        document = Document(
            key="doc-001",
            metadata=metadata,
            storage_key="docs/test.pdf"
        )
        assert document.key == "doc-001"
        assert document.metadata == metadata
        assert document.storage_key == "docs/test.pdf"

    def test_document_to_dict(self):
        """Test converting Document to dictionary"""
        now = datetime(2024, 1, 1, 12, 0, 0)
        metadata = DocumentMetadata(
            name="test.pdf",
            content_type="application/pdf",
            size=1024,
            created_at=now,
            updated_at=now
        )
        document = Document(
            key="doc-001",
            metadata=metadata,
            storage_key="docs/test.pdf"
        )
        document_dict = document.to_dict()

        assert document_dict["key"] == "doc-001"
        assert document_dict["storage_key"] == "docs/test.pdf"
        assert "metadata" in document_dict
        assert document_dict["metadata"]["name"] == "test.pdf"

    def test_document_from_dict(self):
        """Test creating Document from dictionary"""
        now_str = "2024-01-01T12:00:00"
        document_dict = {
            "key": "doc-001",
            "storage_key": "docs/test.pdf",
            "metadata": {
                "name": "test.pdf",
                "content_type": "application/pdf",
                "size": 1024,
                "created_at": now_str,
                "updated_at": now_str
            }
        }

        document = Document.from_dict(document_dict)

        assert document.key == "doc-001"
        assert document.storage_key == "docs/test.pdf"
        assert document.metadata.name == "test.pdf"
        assert document.metadata.content_type == "application/pdf"

    def test_document_round_trip(self):
        """Test Document serialization round trip"""
        now = datetime(2024, 1, 1, 12, 0, 0)
        metadata = DocumentMetadata(
            name="test.pdf",
            content_type="application/pdf",
            size=1024,
            created_at=now,
            updated_at=now
        )
        original_document = Document(
            key="doc-001",
            metadata=metadata,
            storage_key="docs/test.pdf"
        )

        document_dict = original_document.to_dict()
        restored_document = Document.from_dict(document_dict)

        assert restored_document.key == original_document.key
        assert restored_document.metadata.name == original_document.metadata.name
        assert restored_document.storage_key == original_document.storage_key
