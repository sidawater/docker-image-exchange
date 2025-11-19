"""
server settings for FastAPI application
"""

from dataclasses import dataclass
from .container import Attr, EnvLoadable
from .base import PartMixin, DictMixin


@dataclass
class ServerConfig(EnvLoadable, PartMixin, DictMixin):
    """
    FastAPI server configuration
    """
    _prefix = "server_"

    host: str = Attr(default="0.0.0.0", env="SERVER_HOST")
    port: int = Attr(default=8000, env="SERVER_PORT")
    reload: bool = Attr(default=False, env="SERVER_RELOAD")

    @property
    def debug(self) -> bool:
        return self.reload


def init_server_config():
    server_config = ServerConfig.load_from_env()
    return server_config
