from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy import String, Integer, DateTime, Text, JSON, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class DictMixin:
    def as_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary

        :returns: dict, model data as dictionary
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Base(AsyncAttrs, DeclarativeBase, DictMixin):
    """Base class for all models with async support"""
    pass
