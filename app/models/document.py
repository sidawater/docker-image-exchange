from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base
from .tag import Tag


class Document(Base):
    """
    ORM model for documents without foreign keys
    """
    __tablename__ = 'documents'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True, index=True)
    is_audited: Mapped[Boolean] = mapped_column(Boolean, nullable=False, default=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    custom_fields: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Document to dictionary

        :returns: dict, document data as dictionary
        """
        return {
            "id": self.id,
            "name": self.name,
            "content_type": self.content_type,
            "size": self.size,
            "storage_key": self.storage_key,
            "description": self.description,
            "custom_fields": self.custom_fields,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_document_object(cls, document_obj) -> "Document":
        """
        Create Document ORM object from schema Document object

        :param document_obj: Document, schema document object
        :returns: Document, ORM document object
        """
        return cls(
            id=document_obj.key,
            name=document_obj.metadata.name,
            content_type=document_obj.metadata.content_type,
            size=document_obj.metadata.size,
            storage_key=document_obj.storage_key,
            description=document_obj.metadata.description,
            custom_fields=document_obj.metadata.custom_fields,
            created_at=document_obj.metadata.created_at,
            updated_at=document_obj.metadata.updated_at
        )

    def to_document_object(self, tags: List[Tag] = None, aliases: List[str] = None):
        """
        Convert to schema Document object

        :param tags: List[Tag], list of tags for this document
        :param aliases: List[str], list of aliases for this document
        :returns: Document, schema document object
        """
        from core.schema import Document, DocumentMetadata, Tag as SchemaTag

        # Convert ORM tags to schema tags
        schema_tags = [
            SchemaTag(name=tag.name, display_name=tag.display_name)
            for tag in (tags or [])
        ]

        metadata = DocumentMetadata(
            name=self.name,
            content_type=self.content_type,
            size=self.size,
            created_at=self.created_at,
            updated_at=self.updated_at,
            description=self.description,
            tags=schema_tags,
            custom_fields=self.custom_fields,
            aliases=aliases or []
        )

        return Document(
            key=self.id,
            metadata=metadata,
            storage_key=self.storage_key
        )


class DocumentTagAssociation(Base):
    """
    Association table for documents and tags (manual many-to-many)
    """
    __tablename__ = 'document_tags'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    tag_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert association to dictionary

        :returns: dict, association data as dictionary
        """
        return {
            "id": self.id,
            "document_id": self.document_id,
            "tag_id": self.tag_id,
            "created_at": self.created_at.isoformat()
        }


class DocumentAlias(Base):
    """
    ORM model for document aliases without foreign keys
    """
    __tablename__ = 'document_aliases'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alias: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    document_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert DocumentAlias to dictionary

        :returns: dict, alias data as dictionary
        """
        return {
            "id": self.id,
            "alias": self.alias,
            "document_id": self.document_id,
            "created_at": self.created_at.isoformat()
        }
