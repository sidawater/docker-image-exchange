"""
common database settings
"""

from typing import Optional
from dataclasses import dataclass
from .container import Attr, EnvLoadable
from .base import PartMixin, DictMixin


@dataclass
class DatabaseConfig(EnvLoadable, PartMixin, DictMixin):
    _prefix: str = "db_"

    url: str = Attr(default='', env="DATABASE_URL")
    pool_size: int = Attr(default=0, env="DATABASE_POOL_SIZE")
    max_overflow: int = Attr(default=0, env="DATABASE_MAX_OVERFLOW")
    echo: bool = Attr(default=False, env="DATABASE_ECHO")
    echo_pool: bool = Attr(default=False, env="DATABASE_ECHO_POOL")
    pool_pre_ping: bool = Attr(default=True, env="DATABASE_POOL_PRE_PING")
    pool_recycle: int = Attr(default=3600, env="DATABASE_POOL_RECYCLE")
    
    # timeout
    connect_timeout: int = Attr(default=30, env="DATABASE_CONNECT_TIMEOUT")
    command_timeout: Optional[int] = Attr(default=None, env="DATABASE_COMMAND_TIMEOUT")
    
    # SSL
    ssl_mode: Optional[str] = Attr(default=None, env="DATABASE_SSL_MODE")
    ssl_cert: Optional[str] = Attr(default=None, env="DATABASE_SSL_CERT")
    ssl_key: Optional[str] = Attr(default=None, env="DATABASE_SSL_KEY")
    ssl_ca: Optional[str] = Attr(default=None, env="DATABASE_SSL_CA")


def init_database_config():
    database_config = DatabaseConfig.load_from_env()
    return database_config
