"""Module definition"""

from typing import AsyncIterator, Dict, List, Optional, Any, Union

from react.config.llm import LLMConfig
from .client import LLMClient, LLMClientFactory, ChatCompletion, ChatCompletionChunk

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None


class OpenAIClient(LLMClient):
    """
    OpenAI

    OpenAI APIAPI（Azure、）
    """

    def __init__(self, config: LLMConfig) -> None:
        """
        OpenAI

        :param config: LLM
        """
        super().__init__(config)

        if AsyncOpenAI is None:
            raise ImportError("openai，: pip install openai")

        base_url = config.base_url
        if base_url and not base_url.endswith('/v1'):
            base_url = base_url.rstrip('/') + '/v1'

        self._client = AsyncOpenAI(
            api_key=config.api_key,
            base_url=base_url,
            timeout=60.0
        )

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
        model = model or self.config.model
        temperature = temperature if temperature is not None else self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens

        if stream:
            return self._stream_chat(
                messages, model, temperature, max_tokens, tools, **kwargs
            )
        else:
            return await self._non_stream_chat(
                messages, model, temperature, max_tokens, tools, **kwargs
            )

    async def _non_stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> ChatCompletion:
        """
        

        :param messages: 
        :param model: 
        :param temperature: 
        :param max_tokens: token
        :param tools: 
        :return: 
        """
        try:
            request_kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                **kwargs
            }
            # if tools:
            #     request_kwargs["tools"] = tools
            #     request_kwargs["tool_choice"] = "auto"

            response = await self._client.chat.completions.create(**request_kwargs)

            choice = response.choices[0]
            content = choice.message.content or ""

            tool_calls = None
            if choice.message.tool_calls:
                tool_calls = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in choice.message.tool_calls
                ]

            raw_response = {
                "id": response.id,
                "model": response.model,
                "choices": [
                    {
                        "message": {
                            "role": choice.message.role,
                            "content": content,
                            "tool_calls": tool_calls
                        },
                        "finish_reason": choice.finish_reason
                    }
                ]
            }

            return ChatCompletion(
                content=content,
                model=response.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                },
                finish_reason=choice.finish_reason or "",
                raw_response=raw_response
            )

        except Exception:
            raise

    async def _stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> AsyncIterator[ChatCompletionChunk]:
        """
        

        :param messages: 
        :param model: 
        :param temperature: 
        :param max_tokens: token
        :param tools: 
        :return: 
        """
        try:
            request_kwargs = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": True,
                **kwargs
            }

            if tools:
                request_kwargs["tools"] = tools
                request_kwargs["tool_choice"] = "auto"

            stream = await self._client.chat.completions.create(**request_kwargs)

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield ChatCompletionChunk(
                        delta=chunk.choices[0].delta.content,
                        model=chunk.model,
                        finish_reason=chunk.choices[0].finish_reason
                    )

        except Exception:
            raise

    async def close(self) -> None:
        """Module definition"""
        if self._client:
            await self._client.close()


LLMClientFactory.register("openai", OpenAIClient)
