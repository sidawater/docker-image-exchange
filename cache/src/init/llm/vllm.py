"""
Asynchronous client class for interacting with vLLM OpenAI-compatible servers,
supporting both streaming and non-streaming calls.

This class encapsulates the OpenAI official asynchronous client and preserves
parameter passing for vLLM-specific features (such as chat_template_kwargs),
but does not perform any additional parsing of response content.
"""

from typing import Union, AsyncGenerator, Optional

from openai import AsyncOpenAI


class AsyncVLLMClient:

    def __init__(
        self,
        base_url: str,
        default_model: str,
        api_key: str = "dummy_key",
        default_max_tokens: int = 2048,
        default_temperature: float = 0.1,
        default_top_p: float = 0.8,
    ):
        """
        Initialize AsyncVLLMClient.

        :param base_url: Root address of the vLLM service, e.g. "http://localhost:8000/v1"
        :param default_model: Default model name to use
        :param api_key: API key, vLLM services typically don't validate, can use any string
        :param default_max_tokens: Default maximum number of tokens to generate
        :param default_temperature: Default temperature parameter
        :param default_top_p: Default top_p parameter
        """
        if not base_url.endswith('/v1'):
            self.base_url = base_url.rstrip('/') + '/v1'
        else:
            self.base_url = base_url
            
        self.api_key = api_key
        self.default_model = default_model
        self.default_max_tokens = default_max_tokens
        self.default_temperature = default_temperature
        self.default_top_p = default_top_p

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    async def _call_non_streaming(self, params: dict) -> str:
        """Private async method for handling non-streaming requests."""
        response = await self.client.chat.completions.create(**params)
        content = response.choices[0].message.content or ''
        return content

    async def _call_streaming(self, params: dict) -> AsyncGenerator[str, None]:
        """Private async method for handling streaming requests, which is an async generator."""
        response = await self.client.chat.completions.create(**params)
        async for chunk in response:
            if not chunk.choices:
                continue
            delta_content = chunk.choices[0].delta.content or ""
            if delta_content:
                yield delta_content

    async def chat(
        self,
        messages: list,
        model: str,
        stream: bool = False,
        **kwargs
    ) -> Union[str, AsyncGenerator[str, None]]:
        """
        Asynchronously call the model to generate text.

        :param messages: List of messages
        :param model: Model name to use. If None, uses default_model
        :param stream: Whether to enable streaming response. Defaults to False
            - False: Returns complete string
            - True: Returns an async generator that yields text chunks
        :param kwargs: Other optional parameters that override class defaults:
            max_tokens, temperature, top_p
            enable_thinking: Whether to enable thinking mode (only passed as parameter to vLLM)
            use_chat_template_kwargs: Whether to pass chat_template_kwargs to vLLM

        :return: Union[str, AsyncGenerator[str, None]]
            If stream=False, returns an Awaitable of string
            If stream=True, returns an async generator
        """
        model_to_use = model or self.default_model
        if not model_to_use:
            raise ValueError("模型名称未指定，请在调用时传入或在初始化时设置 default_model。")

        max_tokens = kwargs.get('max_tokens', self.default_max_tokens)
        temperature = kwargs.get('temperature', self.default_temperature)
        top_p = kwargs.get('top_p', self.default_top_p)
        enable_thinking = kwargs.get('enable_thinking', False)
        use_chat_template_kwargs = kwargs.get('use_chat_template_kwargs', True)

        params = {
            "model": model_to_use,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stream": stream
        }

        if use_chat_template_kwargs:
            params["extra_body"] = {
                "chat_template_kwargs": {"enable_thinking": enable_thinking}
            }

        if stream:
            return self._call_streaming(params)
        else:
            return await self._call_non_streaming(params)

    async def chat_non_stream(
        self,
        messages: list,
        model: str | None,
        **kwargs
    ) -> str:
        """
        Asynchronously call the model to generate text in non-streaming mode.

        :param messages: List of messages
        :param model: Model name to use. If None, uses default_model
        :param kwargs: Other optional parameters that override class defaults:
            max_tokens, temperature, top_p
            enable_thinking: Whether to enable thinking mode (only passed as parameter to vLLM)
            use_chat_template_kwargs: Whether to pass chat_template_kwargs to vLLM

        :return: Generated text as string
        """
        model_to_use = model or self.default_model
        if not model_to_use:
            raise ValueError("模型名称未指定，请在调用时传入或在初始化时设置 default_model。")

        max_tokens = kwargs.get('max_tokens', self.default_max_tokens)
        temperature = kwargs.get('temperature', self.default_temperature)
        top_p = kwargs.get('top_p', self.default_top_p)
        enable_thinking = kwargs.get('enable_thinking', False)
        use_chat_template_kwargs = kwargs.get('use_chat_template_kwargs', True)

        params = {
            "model": model_to_use,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stream": False
        }

        if use_chat_template_kwargs:
            params["extra_body"] = {
                "chat_template_kwargs": {"enable_thinking": enable_thinking}
            }

        return await self._call_non_streaming(params)

    async def chat_stream(
        self,
        messages: list,
        model: str,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Asynchronously call the model to generate text in streaming mode.

        :param messages: List of messages
        :param model: Model name to use. If None, uses default_model
        :param kwargs: Other optional parameters that override class defaults:
            max_tokens, temperature, top_p
            enable_thinking: Whether to enable thinking mode (only passed as parameter to vLLM)
            use_chat_template_kwargs: Whether to pass chat_template_kwargs to vLLM

        :return: Async generator that yields text chunks
        """
        model_to_use = model or self.default_model
        if not model_to_use:
            raise ValueError("模型名称未指定，请在调用时传入或在初始化时设置 default_model。")

        max_tokens = kwargs.get('max_tokens', self.default_max_tokens)
        temperature = kwargs.get('temperature', self.default_temperature)
        top_p = kwargs.get('top_p', self.default_top_p)
        enable_thinking = kwargs.get('enable_thinking', False)
        use_chat_template_kwargs = kwargs.get('use_chat_template_kwargs', True)

        params = {
            "model": model_to_use,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stream": True
        }

        if use_chat_template_kwargs:
            params["extra_body"] = {
                "chat_template_kwargs": {"enable_thinking": enable_thinking}
            }

        async for chunk in self._call_streaming(params):
            yield chunk

    def __repr__(self) -> str:
        return (
            f"AsyncVLLMClient(base_url='{self.base_url}', "
            f"default_model='{self.default_model}')"
        )


# Global AsyncVLLMClient instance
# This will be initialized by the application startup
vllm_client: AsyncVLLMClient | None = None


def init_vllm_client(
    base_url: str,
    default_model: str,
    api_key: str = "dummy_key",
    default_max_tokens: int = 2048,
    default_temperature: float = 0.1,
    default_top_p: float = 0.8,
) -> AsyncVLLMClient:
    """
    Initialize the global AsyncVLLMClient instance.

    :param base_url: Root address of the vLLM service
    :param default_model: Default model name to use
    :param api_key: API key for authentication
    :param default_max_tokens: Default maximum tokens to generate
    :param default_temperature: Default temperature parameter
    :param default_top_p: Default top_p parameter
    :returns: Initialized AsyncVLLMClient instance
    :raises RuntimeError: If client already initialized
    """
    global vllm_client
    if vllm_client is not None:
        raise RuntimeError("Global vllm_client already initialized.")

    vllm_client = AsyncVLLMClient(
        base_url=base_url,
        default_model=default_model,
        api_key=api_key,
        default_max_tokens=default_max_tokens,
        default_temperature=default_temperature,
        default_top_p=default_top_p,
    )
    return vllm_client


def get_vllm_client() -> AsyncVLLMClient:
    """
    Get the global AsyncVLLMClient instance.

    :returns: Global AsyncVLLMClient instance
    :raises RuntimeError: If client not initialized
    """
    if vllm_client is None:
        raise RuntimeError("Global vllm_client not initialized. Call init_vllm_client() first.")
    return vllm_client


class VLLMManager:
    """
    Manager for multiple AsyncVLLMClient instances with lazy initialization pattern.
    """

    def __init__(self):
        self._clients: dict[str, AsyncVLLMClient] = {}
        self._default_client_code: Optional[str] = None

    def init_client(
        self,
        code: str,
        base_url: str,
        default_model: str,
        api_key: str = "dummy_key",
        default_max_tokens: int = 2048,
        default_temperature: float = 0.1,
        default_top_p: float = 0.8,
        set_as_default: bool = True,
    ) -> None:
        """
        Initialize and register an AsyncVLLMClient with the given code.

        :param code: Unique identifier for this client
        :param base_url: Root address of vLLM service
        :param default_model: Default model name to use
        :param api_key: API key for authentication
        :param default_max_tokens: Default maximum tokens to generate
        :param default_temperature: Default temperature parameter
        :param default_top_p: Default top_p parameter
        :param set_as_default: Whether to set this client as the default client
        :returns: None
        :raises RuntimeError: If client with this code already exists
        """
        if code in self._clients:
            raise RuntimeError(f"Client with code '{code}' already initialized.")

        client = AsyncVLLMClient(
            base_url=base_url,
            default_model=default_model,
            api_key=api_key,
            default_max_tokens=default_max_tokens,
            default_temperature=default_temperature,
            default_top_p=default_top_p,
        )

        self._clients[code] = client

        if set_as_default or self._default_client_code is None:
            self._default_client_code = code

    def init(
        self,
        base_url: str,
        default_model: str,
        api_key: str = "dummy_key",
        default_max_tokens: int = 2048,
        default_temperature: float = 0.1,
        default_top_p: float = 0.8,
    ) -> None:
        """
        Initialize a default AsyncVLLMClient for backward compatibility.

        This method initializes a client with a default code 'default'.

        :param base_url: Root address of vLLM service
        :param default_model: Default model name to use
        :param api_key: API key for authentication
        :param default_max_tokens: Default maximum tokens to generate
        :param default_temperature: Default temperature parameter
        :param default_top_p: Default top_p parameter
        :returns: None
        :raises RuntimeError: If a client already exists (use init_client for multiple clients)
        """
        self.init_client(
            code="default",
            base_url=base_url,
            default_model=default_model,
            api_key=api_key,
            default_max_tokens=default_max_tokens,
            default_temperature=default_temperature,
            default_top_p=default_top_p,
            set_as_default=True,
        )

    def get_client(self, code: Optional[str] = None) -> AsyncVLLMClient:
        """
        Get AsyncVLLMClient instance by code.

        :param code: Client code. If None, returns the default client
        :returns: AsyncVLLMClient instance
        :raises RuntimeError: If client not found
        """
        if code is None:
            code = self._default_client_code

        if code is None or code not in self._clients:
            raise RuntimeError(
                f"Client with code '{code}' not found. "
                f"Available clients: {list(self._clients.keys())}"
            )

        return self._clients[code]

    def remove_client(self, code: str) -> None:
        """
        Remove and destroy an AsyncVLLMClient by code.

        :param code: Client code to remove
        :returns: None
        :raises RuntimeError: If client not found
        """
        if code not in self._clients:
            raise RuntimeError(f"Client with code '{code}' not found.")

        del self._clients[code]

        if self._default_client_code == code:
            self._default_client_code = next(iter(self._clients.keys()), None)

    def list_clients(self) -> list[str]:
        """
        List all registered client codes.

        :returns: List of client codes
        """
        return list(self._clients.keys())

    @property
    def client(self) -> AsyncVLLMClient:
        """
        Get the default AsyncVLLMClient instance.

        :returns: AsyncVLLMClient instance
        :raises RuntimeError: If no clients are initialized
        """
        if not self._clients:
            raise RuntimeError(
                "No clients initialized. Call .init_client() first."
            )

        if self._default_client_code is None:
            self._default_client_code = next(iter(self._clients.keys()))

        return self._clients[self._default_client_code]


vllm_manager: VLLMManager = VLLMManager()


def get_vllm_manager() -> VLLMManager:
    """
    Get the global VLLMManager instance.

    :returns: Global VLLMManager instance
    """
    return vllm_manager


if __name__ == '__main__':
    import asyncio

    async def run():
        client = AsyncVLLMClient(
            base_url='http://10.1.0.4:8000',
            default_model='',
        )

        message = [
            {"role": "user", "content": "say hi to me"}
        ]
        res = await client.chat_non_stream(
            messages=message,
            model='Vision_LLM',
        )
        print(res)
    
    asyncio.run(run())