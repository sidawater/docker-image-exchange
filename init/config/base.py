
from typing import Optional
from dataclasses import dataclass, asdict, fields
from .container import EnvLoadable, Attr


class DictMixin:

    def as_dict(self):
        info = asdict(self)
        info.pop('_prefix', None)
        info = {k: v for k, v in info.items() if v is not None}
        return info


@dataclass
class Settings(EnvLoadable, DictMixin):
    """
    base settings
    """
    
    # application
    app_name: str = Attr(default="OAuth2 Server", env="APP_NAME")
    app_version: str = Attr(default="1.0.0", env="APP_VERSION")
    debug: bool = Attr(default=False, env="DEBUG")
    
    # security
    secret_key: str = Attr(default="your-secret-key-here", env="SECRET_KEY")
    algorithm: str = Attr(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Attr(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # db
    db_url: str = Attr(default='', env="DATABASE_URL")
    db_pool_size: int = Attr(default=0, env="DATABASE_POOL_SIZE")
    db_max_overflow: int = Attr(default=0, env="DATABASE_MAX_OVERFLOW")
    db_echo: bool = Attr(default=False, env="DATABASE_ECHO")
    db_echo_pool: bool = Attr(default=False, env="DATABASE_ECHO_POOL")
    db_pool_pre_ping: bool = Attr(default=True, env="DATABASE_POOL_PRE_PING")
    db_pool_recycle: int = Attr(default=3600, env="DATABASE_POOL_RECYCLE")

    db_connect_timeout: int = Attr(default=30, env="DATABASE_CONNECT_TIMEOUT")
    db_command_timeout: Optional[int] = Attr(default=None, env="DATABASE_COMMAND_TIMEOUT")

    db_ssl_mode: Optional[str] = Attr(default=None, env="DATABASE_SSL_MODE")
    db_ssl_cert: Optional[str] = Attr(default=None, env="DATABASE_SSL_CERT")
    db_ssl_key: Optional[str] = Attr(default=None, env="DATABASE_SSL_KEY")
    db_ssl_ca: Optional[str] = Attr(default=None, env="DATABASE_SSL_CA")

    # Redis
    redis_url: str = Attr(default='', env="REDIS_URL")
    redis_max_connections: int = Attr(default='', env="REDIS_MAX_CONNECTIONS")
    redis_encoding: str = Attr(default="utf-8", env="REDIS_ENCODING")
    redis_decode_responses: bool = Attr(default=True, env="REDIS_DECODE_RESPONSES")

    redis_socket_connect_timeout: int = Attr(default=5, env="REDIS_SOCKET_CONNECT_TIMEOUT")
    redis_socket_timeout: int = Attr(default=5, env="REDIS_SOCKET_TIMEOUT")

    redis_health_check_interval: int = Attr(default=30, env="REDIS_HEALTH_CHECK_INTERVAL")
    redis_retry_on_timeout: bool = Attr(default=True, env="REDIS_RETRY_ON_TIMEOUT")

    redis_ssl: Optional[bool] = Attr(default=None, env="REDIS_SSL")
    redis_ssl_cert_reqs: Optional[str] = Attr(default=None, env="REDIS_SSL_CERT_REQS")
    redis_ssl_ca_certs: Optional[str] = Attr(default=None, env="REDIS_SSL_CA_CERTS")
    redis_ssl_certfile: Optional[str] = Attr(default=None, env="REDIS_SSL_CERTFILE")
    redis_ssl_keyfile: Optional[str] = Attr(default=None, env="REDIS_SSL_KEYFILE")

    redis_serializer: Optional[str] = Attr(default=None, env="REDIS_SERIALIZER")
    redis_compress: Optional[bool] = Attr(default=None, env="REDIS_COMPRESS")

    # minio storage
    storage_backend: str = Attr(default='minio', env="STORAGE_BACKEND")
    storage_bucket_name: str = Attr(default='user-docs', env="STORAGE_BUCKET_NAME")
    storage_endpoint: str = Attr(default='minio.example.com:9000', env="STORAGE_ENDPOINT")
    storage_access_key: str = Attr(default='YOUR_ACCESS_KEY', env="STORAGE_ACCESS_KEY")
    storage_secret_key: str = Attr(default='YOUR_SECRET_KEY', env="STORAGE_SECRET_KEY")
    storage_secure: bool = Attr(default=False, env="STORAGE_SECURE")
    storage_region: Optional[str] = Attr(default=None, env="STORAGE_REGION")
    storage_max_workers: int = Attr(default=10, env="STORAGE_MAX_WORKERS")

    # Server
    server_host: str = Attr(default="0.0.0.0", env="SERVER_HOST")
    server_port: int = Attr(default=8000, env="SERVER_PORT")
    server_reload: bool = Attr(default=False, env="SERVER_RELOAD")

    # CORS
    cors_origins: list = Attr(default_factory=lambda: ["*"], env="CORS_ORIGINS")
    cors_allow_credentials: bool = Attr(default=True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: list = Attr(default_factory=lambda: ["*"], env="CORS_ALLOW_METHODS")
    cors_allow_headers: list = Attr(default_factory=lambda: ["*"], env="CORS_ALLOW_HEADERS")


def init_settings():
    settings = Settings.load_from_env()
    return settings


class PartMixin:

    _prefix: str = None

    @classmethod
    def load_from_settings(cls, settings: Settings):
        if cls._prefix is None:
            raise KeyError('PartMixin must has a prefix')
        
        cls_field_names = {f.name for f in fields(cls)}
        prefix_length = len(cls._prefix)
        
        kv = {
            key[prefix_length:]: value
            for key, value in asdict(settings).items()
            if key.startswith(cls._prefix) and key[prefix_length:] in cls_field_names
        }
        return cls(**kv)
