"""
LLM service settings for vLLM OpenAI-compatible servers.
"""

from dataclasses import dataclass

from .container import EnvLoadable, Attr, DictLoadable
from .base import PartMixin, DictMixin


@dataclass
class LLMConfig(EnvLoadable, PartMixin, DictMixin):
    """
    Configuration for AsyncVLLMClient.

    :param base_url: Root address of vLLM service, e.g. "http://localhost:8000"
    :param default_model: Default model name to use
    :param api_key: API key, vLLM services typically don't validate
    :param default_max_tokens: Default maximum number of tokens to generate
    :param default_temperature: Default temperature parameter
    :param default_top_p: Default top_p parameter
    """
    _prefix: str = "llm_"

    base_url: str = Attr(default='http://localhost:8000', env="LLM_BASE_URL")
    default_model: str = Attr(default='', env="LLM_DEFAULT_MODEL")
    api_key: str = Attr(default='dummy_key', env="LLM_API_KEY")
    default_max_tokens: int = Attr(default=2048, env="LLM_DEFAULT_MAX_TOKENS")
    default_temperature: float = Attr(default=0.1, env="LLM_DEFAULT_TEMPERATURE")
    default_top_p: float = Attr(default=0.8, env="LLM_DEFAULT_TOP_P")


def init_llm_config() -> LLMConfig:
    """
    Initialize LLMConfig from environment variables.

    :returns: LLMConfig instance loaded from environment
    """
    llm_config = LLMConfig.load_from_env()
    return llm_config


@dataclass
class DictLLMConfig(DictLoadable):
    """
    Dictionary-based LLM configuration for AsyncVLLMClient.

    Usage Sample::

        config_dict = {
            "base_url": "http://localhost:8000",
            "default_model": "model-name",
            "api_key": "dummy_key",
            "default_max_tokens": 2048,
            "default_temperature": 0.1,
            "default_top_p": 0.8
        }
        config = DictLLMConfig.load_from_dict(config_dict)

    :param base_url: Root address of vLLM service, e.g. "http://localhost:8000"
    :param default_model: Default model name to use
    :param api_key: API key, vLLM services typically don't validate
    :param default_max_tokens: Default maximum number of tokens to generate
    :param default_temperature: Default temperature parameter
    :param default_top_p: Default top_p parameter
    """
    base_url: str = 'http://localhost:8000'
    default_model: str = ''
    api_key: str = 'dummy_key'
    default_max_tokens: int = 2048
    default_temperature: float = 0.1
    default_top_p: float = 0.8


def init_dict_llm_config(data: dict) -> DictLLMConfig:
    """
    Initialize DictLLMConfig from dictionary.

    :param data: Configuration dictionary
    :returns: DictLLMConfig instance loaded from dictionary
    """
    config = DictLLMConfig.load_from_dict(data)
    return config


@dataclass
class EmbeddingConfig(EnvLoadable, PartMixin, DictMixin):
    _prefix: str = "embedding_"

    base_url: str = Attr(default='http://localhost:11434', env="EMBEDDING_BASE_URL")
    model_name: str = Attr(default='nomic-embed-text', env="EMBEDDING_MODEL_NAME")
    embedding_dim: int = Attr(default=768, env="EMBEDDING_DIM")
    timeout: int = Attr(default=300, env="EMBEDDING_TIMEOUT")
    max_concurrent: int = Attr(default=10, env="EMBEDDING_MAX_CONCURRENT")


def init_embedding_config():
    embedding_config = EmbeddingConfig.load_from_env()
    return embedding_config


@dataclass
class DictEmbeddingConfig(DictLoadable):
    """
    Dictionary-based Embedding configuration.

    Usage Sample::

        config_dict = {
            "base_url": "http://localhost:11434",
            "model_name": "nomic-embed-text",
            "embedding_dim": 768,
            "timeout": 300,
            "max_concurrent": 10
        }
        config = DictEmbeddingConfig.load_from_dict(config_dict)

    :param base_url: Root address of embedding service
    :param model_name: Name of the embedding model
    :param embedding_dim: Dimension of embedding vectors
    :param timeout: Request timeout in seconds
    :param max_concurrent: Maximum concurrent requests
    """
    base_url: str
    model_name: str
    embedding_dim: int = 768
    timeout: int = 300
    max_concurrent: int = 10


def init_dict_embedding_config(data: dict):
    """
    Initialize DictEmbeddingConfig from dictionary.

    :param data: Configuration dictionary
    :returns: DictEmbeddingConfig instance loaded from dictionary
    """
    config = DictEmbeddingConfig.load_from_dict(data)
    return config
