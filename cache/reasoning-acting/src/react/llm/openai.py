"""Module definition"""

from typing import AsyncIterator, Dict, List, Optional, Any, Union

from .schema import LLMConfig, OpenAIConfig
from .client import LLMClient, ChatCompletion, ChatCompletionChunk

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

        init_args = config.init_args()

        base_url = init_args.get("base_url")
        if base_url and not base_url.endswith('/v1'):
            base_url = base_url.rstrip('/') + '/v1'
            init_args["base_url"] = base_url

        self._client = AsyncOpenAI(**init_args)

        self._default_reasoning = False
        if hasattr(config, 'reasoning'):
            self._default_reasoning = config.reasoning

    async def _chat_completion_impl(
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
        """Internal chat completion implementation

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
        model = model or self.config.model
        temperature = temperature if temperature is not None else self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens

        if enable_thinking is None:
            enable_thinking = self._default_reasoning

        if stream:
            return self._stream_chat(
                messages, model, temperature, max_tokens, tools, enable_thinking, **kwargs
            )
        else:
            return await self._non_stream_chat(
                messages, model, temperature, max_tokens, tools, enable_thinking, **kwargs
            )

    async def _non_stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        tools: Optional[List[Dict[str, Any]]] = None,
        enable_thinking: Optional[bool] = None,
        **kwargs
    ) -> ChatCompletion:
        """
        Non-streaming chat completion

        :param messages: Message list
        :param model: Model name
        :param temperature: Temperature
        :param max_tokens: Max tokens
        :param tools: Tools list
        :param enable_thinking: Enable thinking mode
        :param kwargs: Additional arguments
        :return: Chat completion response
        """
        try:
            request_kwargs = self.config.chat_args(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                enable_thinking=enable_thinking,
                **kwargs
            )
            request_kwargs["messages"] = messages

            if tools:
                request_kwargs["tools"] = tools
                request_kwargs["tool_choice"] = "auto"

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
        enable_thinking: Optional[bool] = None,
        **kwargs
    ) -> AsyncIterator[ChatCompletionChunk]:
        """
        Streaming chat completion

        :param messages: Message list
        :param model: Model name
        :param temperature: Temperature
        :param max_tokens: Max tokens
        :param tools: Tools list
        :param enable_thinking: Enable thinking mode
        :param kwargs: Additional arguments
        :return: Async iterator of chat completion chunks
        """
        try:
            request_kwargs = self.config.chat_args(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                enable_thinking=enable_thinking,
                stream=True,
                **kwargs
            )
            request_kwargs["messages"] = messages

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
