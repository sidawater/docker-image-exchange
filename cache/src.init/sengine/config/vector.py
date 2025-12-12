"""
common storage settings
"""

from typing import Optional
from dataclasses import dataclass
from .container import Attr, EnvLoadable
from .base import PartMixin, DictMixin


@dataclass
class QdrantConfig(EnvLoadable, PartMixin, DictMixin):
    _prefix: str = "qdrant_"

    host: str = Attr(default='localhost', env="QDRANT_HOST")
    port: int = Attr(default=6333, env="QDRANT_PORT")
    grpc_port: int = Attr(default=6334, env="QDRANT_GRPC_PORT")
    api_key: Optional[str] = Attr(default=None, env="QDRANT_API_KEY")
    timeout: int = Attr(default=120, env="QDRANT_TIMEOUT")
    prefer_grpc: bool = Attr(default=True, env="QDRANT_PREFER_GRPC")


def init_qdrant_config():
    qdrant_config = QdrantConfig.load_from_env()
    return qdrant_config
