"""LLM Client Module"""

from .schema import (
    LLMConfig,
    OpenAIConfig,
    VllmOpenaiConfig,
    RetryConfig,
    RateLimitConfig,
    LoggingConfig
)

from .client import (
    LLMClient,
    LLMManager,
    ChatCompletion,
    ChatCompletionChunk,
    create_client,
    get_client,
    list_clients,
    close_client,
    close_all_clients,
    llm_manager
)

def _register():
    from .openai import OpenAIClient
    from .vllm import VllmOpenaiClient
    LLMManager.register("openai", OpenAIClient)
    LLMManager.register("vllm_openai", VllmOpenaiClient)

_register()


__all__ = [
    "LLMConfig",
    "OpenAIConfig",
    "VllmOpenaiConfig",
    "RetryConfig",
    "RateLimitConfig",
    "LoggingConfig",
    "LLMClient",
    "LLMManager",
    "ChatCompletion",
    "ChatCompletionChunk",
    "create_client",
    "get_client",
    "list_clients",
    "close_client",
    "close_all_clients",
    "llm_manager",
]

