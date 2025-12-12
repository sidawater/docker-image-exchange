"""
system configuration for kasync module
"""

from dataclasses import dataclass
from .container import Attr, EnvLoadable
from .base import PartMixin, DictMixin


@dataclass
class SystemConfig(EnvLoadable, PartMixin, DictMixin):
    """
    system configuration for kasync module
    """
    _prefix: str = "system_"

    # cache settings
    cache_dir: str = Attr(
        default="/tmp/kasync/cache",
        env="SYSTEM_CACHE_DIR"
    )

    # queue settings
    document_processing_stream: str = Attr(
        default="document_processing",
        env="SYSTEM_DOCUMENT_PROCESSING_STREAM"
    )

    # consumer settings
    consumer_max_retries: int = Attr(
        default=3,
        env="SYSTEM_CONSUMER_MAX_RETRIES"
    )


def init_system_config():
    """
    initialize system configuration from environment variables
    """
    system_config = SystemConfig.load_from_env()
    return system_config
