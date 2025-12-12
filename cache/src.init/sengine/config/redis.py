
"""
common redis settings
"""

from typing import Optional
from dataclasses import dataclass
from .container import EnvLoadable, Attr
from .base import PartMixin, DictMixin


@dataclass
class RedisConfig(EnvLoadable, PartMixin, DictMixin):
    _prefix: str = "redis_"

    url: str = Attr(default='', env="REDIS_URL")
    max_connections: int = Attr(default='', env="REDIS_MAX_CONNECTIONS")
    encoding: str = Attr(default="utf-8", env="REDIS_ENCODING")
    decode_responses: bool = Attr(default=True, env="REDIS_DECODE_RESPONSES")
    
    # timeout
    socket_connect_timeout: int = Attr(default=5, env="REDIS_SOCKET_CONNECT_TIMEOUT")
    socket_timeout: int = Attr(default=5, env="REDIS_SOCKET_TIMEOUT")
    
    # connection pool
    health_check_interval: int = Attr(default=30, env="REDIS_HEALTH_CHECK_INTERVAL")
    retry_on_timeout: bool = Attr(default=True, env="REDIS_RETRY_ON_TIMEOUT")
    
    # SSL
    ssl: Optional[bool] = Attr(default=None, env="REDIS_SSL")
    ssl_cert_reqs: Optional[str] = Attr(default=None, env="REDIS_SSL_CERT_REQS")
    ssl_ca_certs: Optional[str] = Attr(default=None, env="REDIS_SSL_CA_CERTS")
    ssl_certfile: Optional[str] = Attr(default=None, env="REDIS_SSL_CERTFILE")
    ssl_keyfile: Optional[str] = Attr(default=None, env="REDIS_SSL_KEYFILE")
    
    # serialize
    serializer: Optional[str] = Attr(default=None, env="REDIS_SERIALIZER")
    compress: Optional[bool] = Attr(default=None, env="REDIS_COMPRESS")


def init_redis_config():
    redis_config = RedisConfig.load_from_env()
    return redis_config
