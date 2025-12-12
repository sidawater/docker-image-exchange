"""
knowledge models
"""

from typing import Optional, Dict, Any
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, JSON, Boolean, ForeignKey
from .base import Base, TimestampMixin


class Session(Base, TimestampMixin):
    """session model"""
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    meta_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)


class QA(Base, TimestampMixin):
    """qa model"""
    __tablename__ = "qa"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    session_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    qa_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    question_content: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    question_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    answer_content: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    answer_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    session: Mapped["Session"] = relationship(
        back_populates="qa_records",
        cascade="all, delete-orphan"
    )


class Attachment(Base, TimestampMixin):
    """attachment model"""
    __tablename__ = "attachments"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    qa_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("qa.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    attach_key: Mapped[str] = mapped_column(String(255), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(nullable=True)
    storage_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    meta_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    qa: Mapped["QA"] = relationship(
        back_populates="attachments",
        cascade="all, delete-orphan"
    )


Session.qa_records = relationship(
    "QA",
    back_populates="session",
    cascade="all, delete-orphan"
)

QA.attachments = relationship(
    "Attachment",
    back_populates="qa",
    cascade="all, delete-orphan"
)
