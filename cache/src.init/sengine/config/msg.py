"""
消息服务配置
"""

from typing import Optional
from dataclasses import dataclass
from .container import Attr, EnvLoadable
from .base import PartMixin, DictMixin


@dataclass
class MsgConfig(EnvLoadable, PartMixin, DictMixin):
    _prefix: str = "msg_"

    base_url: str = Attr(default='', env="MSG_BASE_URL")
    api_token: str = Attr(default='', env="MSG_API_TOKEN")
    timeout: int = Attr(default=30, env="MSG_TIMEOUT")


def init_msg_config():
    msg_config = MsgConfig.load_from_env()
    return msg_config
