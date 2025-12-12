"""
Message Service Data Models

Defines all data models used by the client, including request and response models.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any


class DictMixin:
    """Dictionary conversion mixin class"""

    def as_dict(self):
        """Convert to dictionary"""
        info = asdict(self)
        info.pop('_prefix', None)
        return {k: v for k, v in info.items() if v is not None}


@dataclass
class QaMessageContent(DictMixin):
    """
    QA message content model

    :param content: Message text content
    :param attaches: Attachment list
    :param attaches_induction: Attachment description list
    """
    content: str = ""
    attaches: Optional[List[Dict[str, Any]]] = field(
        default_factory=list
    )
    attaches_induction: Optional[List[Dict[str, Any]]] = field(
        default_factory=list
    )


@dataclass
class SessionCreateRequest(DictMixin):
    """
    Session creation request model

    :param user_id: User identifier
    :param title: Session title
    :param metadata: Extended metadata
    """
    user_id: str = ""
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SessionUpdateRequest(DictMixin):
    """
    Session update request model

    :param title: Session title
    :param is_active: Active status
    :param metadata: Extended metadata
    """
    title: Optional[str] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class QaCreateRequest(DictMixin):
    """
    QA record creation request model

    :param session_id: Session ID
    :param qa_key: Business key
    :param question: User question
    :param answer: AI answer
    """
    session_id: str = ""
    qa_key: str = ""
    question: QaMessageContent = field(default_factory=QaMessageContent)
    answer: QaMessageContent = field(default_factory=QaMessageContent)


@dataclass
class QaUpdateRequest(DictMixin):
    """
    QA record update request model

    :param question: User question
    :param answer: AI answer
    """
    question: Optional[QaMessageContent] = None
    answer: Optional[QaMessageContent] = None


@dataclass
class PaginationParams(DictMixin):
    """
    Pagination parameters model

    :param offset: Offset, starting from 0
    :param limit: Page size, maximum 100
    :param total: Total record count (optional)
    """
    offset: int = 0
    limit: int = 20
    total: Optional[int] = None

    @property
    def page(self) -> int:
        """
        Computed property: page number (starting from 1)

        :return: Page number
        """
        if self.limit == 0:
            return 1
        return (self.offset // self.limit) + 1

    @property
    def page_size(self) -> int:
        """
        Computed property: page size

        :return: Page size
        """
        return self.limit


@dataclass
class QaSearchParams(PaginationParams):
    """
    QA search parameters model

    :param session_id: Session ID
    :param qa_key: QA business key
    :param start_time: Start time
    :param end_time: End time
    :param only_valid: Whether to return only valid records
    """
    session_id: Optional[str] = None
    qa_key: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    only_valid: bool = False


@dataclass
class ReActCreateRequest(DictMixin):
    """Create ReAct instance request"""
    id: Optional[str] = None
    name: str = ""
    code: str = ""
    description: Optional[str] = None

    llm_provider: str = ""
    llm_model: str = ""
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4096
    llm_timeout: int = 60
    llm_max_retries: int = 3

    mcp_enabled: bool = False
    mcp_servers: Optional[List[Dict[str, Any]]] = None

    rag_enabled: bool = True
    rag_endpoint: Optional[str] = None
    rag_api_key: Optional[str] = None
    rag_top_k: int = 5
    rag_score_threshold: float = 0.7

    max_iterations: int = 10
    timeout: int = 300
    enable_streaming: bool = True
    stream_chunk_size: int = 100

    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


@dataclass
class ReActUpdateRequest(DictMixin):
    """Update ReAct instance request"""
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    is_enabled: Optional[bool] = None

    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_temperature: Optional[float] = None
    llm_max_tokens: Optional[int] = None
    llm_timeout: Optional[int] = None
    llm_max_retries: Optional[int] = None

    mcp_enabled: Optional[bool] = None
    mcp_servers: Optional[List[Dict[str, Any]]] = None

    rag_enabled: Optional[bool] = None
    rag_endpoint: Optional[str] = None
    rag_api_key: Optional[str] = None
    rag_top_k: Optional[int] = None
    rag_score_threshold: Optional[float] = None

    max_iterations: Optional[int] = None
    timeout: Optional[int] = None
    enable_streaming: Optional[bool] = None
    stream_chunk_size: Optional[int] = None

    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


@dataclass
class ReActConfigUpdateRequest(DictMixin):
    """Update ReAct configuration request"""
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReActStatusUpdateRequest(DictMixin):
    """Update ReAct status request"""
    status: str = ""
    reason: Optional[str] = None


@dataclass
class SystemPromptConfigRequest(DictMixin):
    """System prompt configuration request"""
    template: Optional[str] = None


@dataclass
class PlannerPromptConfigRequest(DictMixin):
    """Planning phase prompt configuration request"""
    summary: str = ""
    tools: str = ""
    analysis: str = ""
    tool_name: str = ""


@dataclass
class ExecutorPromptConfigRequest(DictMixin):
    """Execution phase prompt configuration request"""
    tool_descriptions: str = ""
    planning_conclusion: str = ""
    tool_name: str = ""


@dataclass
class PromptConfigRequest(DictMixin):
    """Complete prompt configuration request"""
    system: Optional[SystemPromptConfigRequest] = None
    planner: Optional[PlannerPromptConfigRequest] = None
    executor: Optional[ExecutorPromptConfigRequest] = None


@dataclass
class ReActPromptUpdateRequest(DictMixin):
    """Update ReAct prompt configuration request"""
    prompts: PromptConfigRequest = field(default_factory=PromptConfigRequest)
    validation_enabled: bool = True


@dataclass
class SystemPromptConfigOut(DictMixin):
    """System prompt configuration output"""
    template: str = ""


@dataclass
class PlannerPromptConfigOut(DictMixin):
    """Planning phase prompt configuration output"""
    summary: str = ""
    tools: str = ""
    analysis: str = ""
    tool_name: str = ""


@dataclass
class ExecutorPromptConfigOut(DictMixin):
    """Execution phase prompt configuration output"""
    tool_descriptions: str = ""
    planning_conclusion: str = ""
    tool_name: str = ""


@dataclass
class PromptConfigOut(DictMixin):
    """Complete prompt configuration output"""
    system: Optional[SystemPromptConfigOut] = None
    planner: Optional[PlannerPromptConfigOut] = None
    executor: Optional[ExecutorPromptConfigOut] = None


@dataclass
class ChatCompletionRequest(DictMixin):
    """Chat completion request"""
    message: str = ""
    session_id: str = ""
    stream: bool = True
    react_instance_code: str = ""
    timeout: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ChatMessage(DictMixin):
    """Chat message"""
    role: str = ""
    content: str = ""
    timestamp: Optional[str] = None


@dataclass
class ChatCompletionResponse(DictMixin):
    """Chat completion response"""
    session_id: str = ""
    message_id: Optional[str] = None
    content: str = ""
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    create_time: str = ""


@dataclass
class ChatSessionCreateRequest(DictMixin):
    """Create chat session request"""
    user_id: str = ""
    title: Optional[str] = None
    react_instance_code: str = ""
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


@dataclass
class ChatSessionUpdateRequest(DictMixin):
    """Update chat session request"""
    title: Optional[str] = None
    is_active: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


@dataclass
class ChatSessionOut(DictMixin):
    """Chat session output"""
    session_id: str = ""
    user_id: str = ""
    title: Optional[str] = None
    is_active: bool = False
    react_instance_code: str = ""
    message_count: int = 0
    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    create_time: str = ""
    update_time: str = ""


@dataclass
class ChatHistoryRequest(DictMixin):
    """Chat history request"""
    session_id: str = ""
    limit: int = 50
    offset: int = 0
    order: str = "desc"


@dataclass
class ChatHistoryOut(DictMixin):
    """Chat history output"""
    session_id: str = ""
    total: int = 0
    messages: List[ChatMessage] = field(default_factory=list)


@dataclass
class BatchChatRequest(DictMixin):
    """Batch chat request"""
    requests: List[ChatCompletionRequest] = field(default_factory=list)
    parallel: bool = False


@dataclass
class BatchChatResponse(DictMixin):
    """Batch chat response"""
    results: List[ChatCompletionResponse] = field(default_factory=list)
    success_count: int = 0
    failed_count: int = 0


@dataclass
class ChatConfigRequest(DictMixin):
    """Chat configuration request"""
    default_react_instance: Optional[str] = None
    stream_enabled: bool = True
    stream_chunk_size: int = 100
    timeout: int = 300
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ChatConfigOut(DictMixin):
    """Chat configuration output"""
    config_id: str = ""
    default_react_instance: Optional[str] = None
    stream_enabled: bool = False
    stream_chunk_size: int = 100
    timeout: int = 300
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    create_time: str = ""
    update_time: str = ""


@dataclass
class ReActOut(DictMixin):
    """ReAct instance output"""
    id: str = ""
    name: str = ""
    code: str = ""
    description: Optional[str] = None
    status: str = ""
    is_enabled: bool = False

    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_temperature: Optional[float] = None
    llm_max_tokens: Optional[int] = None
    llm_timeout: Optional[int] = None
    llm_max_retries: Optional[int] = None

    mcp_enabled: bool = False
    mcp_servers: Optional[List[Dict[str, Any]]] = None

    rag_enabled: bool = False
    rag_endpoint: Optional[str] = None
    rag_api_key: Optional[str] = None
    rag_top_k: Optional[int] = None
    rag_score_threshold: Optional[float] = None

    max_iterations: int = 10
    timeout: int = 300
    enable_streaming: bool = True

    metadata: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    create_time: Optional[str] = None
    update_time: Optional[str] = None
