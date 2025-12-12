"""数据模型模块

提供数据库ORM模型定义，包括QA、Session等
"""

from .base import DictMixin, TimestampMixin
from .knowledge import Session, QA, Attachment

__all__ = [
    'DictMixin',
    'TimestampMixin',
    'Session',
    'QA',
    'Attachment',
]
