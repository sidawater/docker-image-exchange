"""LLM Configuration Schemas

This module contains all LLM-related data structures and configuration schemas.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List


@dataclass
class LLMConfig:
    """Base LLM configuration

    :param provider: Provider name (e.g., 'openai', 'vllm_openai')
    :param model: Model name or path
    :param api_key: API key for authentication
    :param base_url: Base URL for the API endpoint
    :param temperature: Sampling temperature (default: 0.1)
    :param max_tokens: Maximum tokens to generate (default: 4096)
    :param timeout: Request timeout in seconds (default: 60)
    :param max_retries: Maximum number of retries (default: 3)
    :param retry_delay: Delay between retries in seconds (default: 1)
    :param proxy: Proxy URL for HTTP requests
    :param headers: Custom HTTP headers
    :param extra_params: Additional provider-specific parameters
    """
    provider: str
    model: str
    api_key: str
    base_url: Optional[str] = None
    temperature: float = 0.1
    max_tokens: int = 4096
    timeout: float = 60.0
    max_retries: int = 3
    retry_delay: float = 1.0
    proxy: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    extra_params: Dict[str, Any] = field(default_factory=dict)

    def init_args(self) -> Dict[str, Any]:
        """Get arguments for client initialization

        :return: Dictionary of initialization arguments
        """
        return {
            "api_key": self.api_key,
            "base_url": self.base_url,
            "timeout": self.timeout
        }

    def chat_args(self, **overrides: Any) -> Dict[str, Any]:
        """Get arguments for chat completion

        :param overrides: Arguments to override
        :return: Dictionary of chat completion arguments
        """
        args = {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        args.update(self.extra_params)
        args.update(overrides)
        return args


@dataclass
class OpenAIConfig(LLMConfig):
    """OpenAI-specific configuration

    :param organization: OpenAI organization ID
    :param api_version: API version (default: 'v1')
    :param reasoning: Enable reasoning mode
    :param reasoning_effort: Reasoning effort level ('low', 'medium', 'high')
    :param include_reasoning: Whether to include reasoning in response
    :param top_p: Nucleus sampling parameter
    :param frequency_penalty: Frequency penalty
    :param presence_penalty: Presence penalty
    :param stop: Stop sequences
    :param seed: Random seed for reproducibility
    """
    organization: Optional[str] = None
    api_version: str = "v1"
    reasoning: bool = False
    reasoning_effort: Optional[str] = None
    include_reasoning: bool = False
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop: Optional[List[str]] = None
    seed: Optional[int] = None

    def __post_init__(self) -> None:
        """Set provider to 'openai' if not specified"""
        if not self.provider:
            self.provider = "openai"

    def init_args(self) -> Dict[str, Any]:
        """Get arguments for OpenAI client initialization

        :return: Dictionary of initialization arguments
        """
        args = super().init_args()
        args["organization"] = self.organization
        return args

    def chat_args(
        self,
        enable_thinking: Optional[bool] = None,
        **overrides: Any
    ) -> Dict[str, Any]:
        """Get arguments for OpenAI chat completion

        :param enable_thinking: Override reasoning mode
        :param overrides: Arguments to override
        :return: Dictionary of chat completion arguments
        """
        args = super().chat_args()

        if self.reasoning and enable_thinking is None:
            enable_thinking = self.reasoning

        if enable_thinking is not None:
            args["reasoning_effort"] = "high" if enable_thinking else "low"
            args["include_reasoning"] = enable_thinking

        if self.top_p is not None:
            args["top_p"] = self.top_p
        if self.frequency_penalty is not None:
            args["frequency_penalty"] = self.frequency_penalty
        if self.presence_penalty is not None:
            args["presence_penalty"] = self.presence_penalty
        if self.stop is not None:
            args["stop"] = self.stop
        if self.seed is not None:
            args["seed"] = self.seed

        args.update(overrides)
        return args


@dataclass
class VllmOpenaiConfig(LLMConfig):
    """vLLM OpenAI-compatible configuration

    :param chat_template_kwargs: Chat template arguments (e.g., enable_thinking)
    :param reasoning: Enable reasoning/thinking mode
    :param top_p: Nucleus sampling parameter
    :param top_k: Top-k sampling parameter
    :param stream: Default stream mode
    :param skip_special_tokens: Whether to skip special tokens
    :param spaces_between_special_tokens: Spaces between special tokens
    :param add_special_tokens: Whether to add special tokens
    """
    chat_template_kwargs: Optional[Dict[str, Any]] = None
    reasoning: bool = False
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    stream: bool = False
    skip_special_tokens: bool = True
    spaces_between_special_tokens: bool = True
    add_special_tokens: bool = True

    def __post_init__(self) -> None:
        """Set provider to 'vllm_openai' if not specified"""
        if not self.provider:
            self.provider = "vllm_openai"

    def init_args(self) -> Dict[str, Any]:
        """Get arguments for vLLM OpenAI client initialization

        :return: Dictionary of initialization arguments
        """
        return super().init_args()

    def chat_args(
        self,
        enable_thinking: Optional[bool] = None,
        **overrides: Any
    ) -> Dict[str, Any]:
        """Get arguments for vLLM chat completion

        :param enable_thinking: Override reasoning mode
        :param overrides: Arguments to override
        :return: Dictionary of chat completion arguments
        """
        args = super().chat_args()

        if self.reasoning and enable_thinking is None:
            enable_thinking = self.reasoning

        if enable_thinking is not None:
            chat_template_kwargs = {"enable_thinking": enable_thinking}
            if self.chat_template_kwargs:
                chat_template_kwargs.update(self.chat_template_kwargs)
            args["extra_body"] = {"chat_template_kwargs": chat_template_kwargs}
        elif self.chat_template_kwargs:
            args["extra_body"] = {"chat_template_kwargs": self.chat_template_kwargs}

        if self.top_p is not None:
            args["top_p"] = self.top_p
        if self.top_k is not None:
            args["top_k"] = self.top_k
        if self.stream:
            args["stream"] = self.stream
        if not self.skip_special_tokens:
            args["skip_special_tokens"] = self.skip_special_tokens
        if not self.spaces_between_special_tokens:
            args["spaces_between_special_tokens"] = self.spaces_between_special_tokens
        if not self.add_special_tokens:
            args["add_special_tokens"] = self.add_special_tokens

        args.update(overrides)
        return args


@dataclass
class RetryConfig:
    """Retry configuration for failed requests

    :param max_attempts: Maximum number of retry attempts
    :param base_delay: Base delay in seconds
    :param max_delay: Maximum delay in seconds
    :param exponential_base: Base for exponential backoff
    :param jitter: Whether to add random jitter
    """
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass
class RateLimitConfig:
    """Rate limiting configuration

    :param requests_per_minute: Maximum requests per minute
    :param requests_per_second: Maximum requests per second
    :param tokens_per_minute: Maximum tokens per minute
    :param burst_size: Burst size for token bucket
    """
    requests_per_minute: Optional[int] = None
    requests_per_second: Optional[float] = None
    tokens_per_minute: Optional[int] = None
    burst_size: int = 100


@dataclass
class LoggingConfig:
    """Logging configuration

    :param level: Log level (DEBUG, INFO, WARNING, ERROR)
    :param format: Log format string
    :param enable_request_logging: Whether to log requests
    :param enable_response_logging: Whether to log responses
    :param redact_sensitive_data: Whether to redact sensitive data
    """
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    enable_request_logging: bool = False
    enable_response_logging: bool = False
    redact_sensitive_data: bool = True
