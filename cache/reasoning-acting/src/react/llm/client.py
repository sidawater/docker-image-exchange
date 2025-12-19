"""Module definition"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Dict, List, Optional, Any, Type, Union

from .schema import LLMConfig


@dataclass
class ChatCompletion:
    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: str = ""
    raw_response: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChatCompletionChunk:
    delta: str
    model: str
    finish_reason: Optional[str] = None


class LLMClient(ABC):

    def __init__(self, config: LLMConfig) -> None:
        """
        Initialize LLM client

        :param config: LLM configuration
        """
        self.config = config

    @abstractmethod
    async def _chat_completion_impl(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Union[ChatCompletion, AsyncIterator[ChatCompletionChunk]]:
        """Internal implementation method

        :param messages: Message list
        :param kwargs: Additional arguments
        :return: Chat completion response
        """
        pass

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False,
        enable_thinking: Optional[bool] = None,
        **kwargs
    ) -> Union[ChatCompletion, AsyncIterator[ChatCompletionChunk]]:
        """Create chat completion

        :param messages: Message list
        :param model: Model name
        :param temperature: Temperature
        :param max_tokens: Max tokens
        :param tools: Tools list
        :param stream: Enable streaming
        :param enable_thinking: Enable thinking mode
        :param kwargs: Additional arguments
        :return: Chat completion response
        """
        return await self._chat_completion_impl(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            tools=tools,
            stream=stream,
            enable_thinking=enable_thinking,
            **kwargs
        )

    async def close(self) -> None:
        """Close client session"""
        pass


class LLMManager:
    """Manager for LLM clients - simple, no factory pattern"""

    _REGISTRY = {}

    def __init__(self) -> None:
        self._clients: Dict[str, LLMClient] = {}
        self._configs: Dict[str, LLMConfig] = {}

    @classmethod
    def register(cls, provider: str, client_class: Type[LLMClient]) -> None:
        """Register a client class to the registry

        :param provider: Provider name
        :param client_class: Client class
        """
        cls._REGISTRY[provider.lower()] = client_class

    def create(
        self,
        code: str,
        config: LLMConfig
    ) -> LLMClient:
        """Create and cache LLM client

        :param code: Unique identifier for the client
        :param config: LLM configuration
        :return: LLM client instance
        """
        if code in self._clients:
            return self._clients[code]

        provider = config.provider.lower()
        client_class = self._REGISTRY.get(provider)
        if not client_class:
            available = ", ".join(self._REGISTRY.keys())
            raise ValueError(
                f"Unsupported provider: {provider}. Available: {available}"
            )

        client = client_class(config)
        self._clients[code] = client
        return client

    def get(self, code: str) -> Optional[LLMClient]:
        """Get cached client

        :param code: Client identifier
        :return: Client instance or None
        """
        return self._clients.get(code)

    def remove(self, code: str) -> None:
        """Remove client from cache

        :param code: Client identifier
        """
        if code in self._clients:
            del self._clients[code]

    async def close(self, code: str) -> None:
        """Close and remove client

        :param code: Client identifier
        """
        client = self._clients.get(code)
        if client:
            await client.close()
            del self._clients[code]

    async def close_all(self) -> None:
        """Close all clients"""
        for code in list(self._clients.keys()):
            await self.close(code)

    def list_clients(self) -> List[str]:
        """List all client codes

        :return: List of client codes
        """
        return list(self._clients.keys())


llm_manager = LLMManager()


def create_client(code: str, config: LLMConfig) -> LLMClient:
    """Create LLM client using global manager

    :param code: Unique identifier for the client
    :param config: LLM configuration
    :return: LLM client instance
    """
    return llm_manager.create(code, config)


def get_client(code: str) -> Optional[LLMClient]:
    """Get cached LLM client

    :param code: Client identifier
    :return: Client instance or None
    """
    return llm_manager.get(code)


def list_clients() -> List[str]:
    """List all client codes

    :return: List of client codes
    """
    return llm_manager.list_clients()


async def close_client(code: str) -> None:
    """Close and remove client

    :param code: Client identifier
    """
    await llm_manager.close(code)


async def close_all_clients() -> None:
    """Close all clients"""
    await llm_manager.close_all()
