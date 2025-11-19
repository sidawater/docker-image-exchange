from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any, List


@dataclass
class TagDomain:
    """
    tag domain with name and optional display name
    """

    name: str
    display_name: str = ""


@dataclass
class Tag:
    """
    Document tag with name and display name
    """
    name: str
    tag_domain: str
    display_name: str


    def to_dict(self) -> dict:
        """
        Convert Tag to dictionary
        
        :returns: dict, tag data as dictionary
        """
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Tag":
        """
        Create Tag from dictionary
        
        :param data: dict, dictionary containing tag data
        :returns: Tag, created Tag object
        """
        return cls(**data)


@dataclass
class DocumentMetadata:
    """
    Document metadata with file information and custom fields
    
    All datetime values are in UTC
    """
    name: str
    content_type: str
    size: int
    created_at: datetime
    updated_at: datetime
    description: Optional[str] = None
    tags: List[Tag] = field(default_factory=list)
    custom_fields: Optional[Dict[str, Any]] = None
    aliases: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """
        Convert DocumentMetadata to dictionary
        
        :returns: dict, metadata as serializable dictionary
        """
        d = asdict(self)
        d["created_at"] = self.created_at.isoformat()
        d["updated_at"] = self.updated_at.isoformat()
        d["tags"] = [tag.to_dict() for tag in self.tags]
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "DocumentMetadata":
        """
        Create DocumentMetadata from dictionary
        
        :param data: dict, dictionary containing metadata
        :returns: DocumentMetadata, created metadata object
        """
        data = data.copy()
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        data["tags"] = [Tag.from_dict(tag_data) for tag_data in data.get("tags", [])]
        return cls(**data)


@dataclass
class Document:
    """
    Document object containing metadata and storage information
    
    - key: Unique document identifier
    - metadata: Document metadata and file information  
    - storage_key: Storage path in MinIO (object key)
    """
    key: str
    metadata: DocumentMetadata
    storage_key: str

    def to_dict(self) -> dict:
        """
        Convert Document to dictionary
        
        :returns: dict, document as serializable dictionary
        """
        return {
            "key": self.key,
            "metadata": self.metadata.to_dict(),
            "storage_key": self.storage_key,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Document":
        """
        Create Document from dictionary
        
        :param data: dict, dictionary containing document data
        :returns: Document, created document object
        """
        return cls(
            key=data["key"],
            metadata=DocumentMetadata.from_dict(data["metadata"]),
            storage_key=data["storage_key"],
        )
