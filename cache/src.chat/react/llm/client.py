"""Module definition"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator, Dict, List, Optional, Any, Type, Union

from react.config.llm import LLMConfig


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
    """
    LLM

    LLM
    """

    def __init__(self, config: LLMConfig) -> None:
        """
        

        :param config: LLM
        """
        self.config = config

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[ChatCompletion, AsyncIterator[ChatCompletionChunk]]:
        """
        

        :param messages: 
        :param model: 
        :param temperature: 
        :param max_tokens: token
        :param tools: 
        :param stream: 
        :return: 
        """
        pass

    async def close(self) -> None:
        """Module definition"""
        pass


class LLMClientFactory:
    
    _clients: Dict[str, Type[LLMClient]] = {}

    @classmethod
    def register(cls, provider: str, client_class: Type[LLMClient]) -> None:
        """
        

        :param provider: 
        :param client_class: 
        """
        cls._clients[provider.lower()] = client_class

    @classmethod
    def create(cls, config: LLMConfig) -> LLMClient:
        """
        

        :param config: LLM
        :return: 
        :raises ValueError: provider
        """
        provider = config.provider.lower()

        if provider not in cls._clients:
            available = ", ".join(cls._clients.keys()) or ""
            raise ValueError(
                f"LLM provider: {provider}, : {available}"
            )

        client_class = cls._clients[provider]
        return client_class(config)

    @classmethod
    def list_providers(cls) -> List[str]:
        """
        provider

        :return: provider
        """
        return list(cls._clients.keys())
