from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
from .base import Base
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy import String, Integer, DateTime, Text, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column


class TagDomain(Base):
    __tablename__ = 'tag_domain'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)


class Tag(Base):
    """
    ORM model for document tags without foreign keys
    """
    __tablename__ = 'tags'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert Tag to dictionary
        
        :returns: dict, tag data as dictionary
        """
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Tag":
        """
        Create Tag from dictionary
        
        :param data: dict, dictionary containing tag data
        :returns: Tag, created Tag object
        """
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data["name"],
            display_name=data["display_name"]
        )

