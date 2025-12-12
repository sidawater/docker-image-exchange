"""基础模型类

提供所有模型的基础类和数据模型
"""

from typing import Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, func


class DictMixin:
    """模型转字典混入类

    提供将模型实例转换为字典的功能
    """

    def as_dict(self) -> Dict[str, Any]:
        """将模型转换为字典

        :returns: 模型数据的字典
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class TimestampMixin:
    """时间戳混入类

    提供创建时间和更新时间字段
    """

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
    """所有模型的基类，支持异步

    所有数据模型都应该继承此类
    """
    pass
