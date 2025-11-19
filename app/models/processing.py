from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base


class DocumentProcessing(Base):
    """
    ORM model for document processing status
    """
    __tablename__ = 'document_processing'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")  # pending, processing, failed, done
    step_counts: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    current_step: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    processing_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    processing_updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert DocumentProcessing to dictionary

        :returns: dict, processing data as dictionary
        """
        return {
            "id": self.id,
            "document_id": self.document_id,
            "status": self.status,
            "step_counts": self.step_counts,
            "current_step": self.current_step,
            "processing_data": self.processing_data,
            "processing_updated_at": self.processing_updated_at.isoformat(),
            "created_at": self.created_at.isoformat()
        }


class DocumentReview(Base):
    """
    ORM model for document review status
    """
    __tablename__ = 'document_reviews'

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    review_state: Mapped[str] = mapped_column(String(50), nullable=False, default="unreviewed")  # unreviewed, approved, rejected
    review_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    review_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    review_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert DocumentReview to dictionary

        :returns: dict, review data as dictionary
        """
        return {
            "id": self.id,
            "document_id": self.document_id,
            "review_state": self.review_state,
            "review_by": self.review_by,
            "review_comment": self.review_comment,
            "review_updated_at": self.review_updated_at.isoformat() if self.review_updated_at else None,
            "created_at": self.created_at.isoformat()
        }