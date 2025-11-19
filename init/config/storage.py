"""
common storage settings
"""

from typing import Optional
from dataclasses import dataclass
from .container import Attr, EnvLoadable
from .base import PartMixin, DictMixin


@dataclass
class StorageConfig(EnvLoadable, PartMixin, DictMixin):
    _prefix: str = "storage_"

    backend: str = Attr(default='minio', env="STORAGE_BACKEND")
    bucket_name: str = Attr(default='user-docs', env="STORAGE_BUCKET_NAME")
    endpoint: str = Attr(default='minio.example.com:9000', env="STORAGE_ENDPOINT")
    access_key: str = Attr(default='YOUR_ACCESS_KEY', env="STORAGE_ACCESS_KEY")
    secret_key: str = Attr(default='YOUR_SECRET_KEY', env="STORAGE_SECRET_KEY")
    secure: bool = Attr(default=False, env="STORAGE_SECURE")
    region: Optional[str] = Attr(default=None, env="STORAGE_REGION")
    max_workers: int = Attr(default=10, env="STORAGE_MAX_WORKERS")


def init_storage_config():
    storage_config = StorageConfig.load_from_env()
    return storage_config
