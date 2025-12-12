from typing import Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, func


class DictMixin:
    """Mixin to convert model to dictionary"""
    def as_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary

        :returns: dict, model data as dictionary
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class TimestampMixin:
    """Mixin to add timestamp fields"""
    create_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        comment="创建时间"
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )


class Base(AsyncAttrs, DeclarativeBase, DictMixin):
    """Base class for all models with async support"""
    pass
