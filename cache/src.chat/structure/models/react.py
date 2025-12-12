"""Meta-ReAct 模型定义

支持配置化的智能推理架构，包括：
- LLM 配置
- MCP 工具配置
- 提示词模板管理
- 决策规则配置
- 流程配置
- 流式输出配置
- ReAct 实例管理
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, JSON, Boolean, Integer, Float, ForeignKey, select
from .base import Base, TimestampMixin, DictMixin


class LLMConfig(Base, TimestampMixin, DictMixin):
    """LLM 配置模型

    存储大语言模型相关配置信息
    """

    __tablename__ = "llm_config"

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        comment="配置ID"
    )
    provider: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="LLM提供商 (如: openai, anthropic)"
    )
    model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="模型名称"
    )
    api_key: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="API密钥"
    )
    base_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="API基础URL"
    )
    temperature: Mapped[float] = mapped_column(
        Float,
        default=0.1,
        nullable=False,
        comment="温度参数"
    )
    max_tokens: Mapped[int] = mapped_column(
        Integer,
        default=4096,
        nullable=False,
        comment="最大令牌数"
    )
    timeout: Mapped[int] = mapped_column(
        Integer,
        default=60,
        nullable=False,
        comment="超时时间(秒)"
    )
    max_retries: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
        comment="最大重试次数"
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用"
    )


class MCPConfig(Base, TimestampMixin, DictMixin):
    """MCP 配置模型

    存储Model Context Protocol相关配置
    """

    __tablename__ = "mcp_config"

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        comment="配置ID"
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否启用MCP"
    )
    connection_timeout: Mapped[int] = mapped_column(
        Integer,
        default=30,
        nullable=False,
        comment="连接超时(秒)"
    )
    reconnect_attempts: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
        comment="重连次数"
    )
    servers: Mapped[Optional[List[Dict[str, Any]]]] = mapped_column(
        JSON,
        nullable=True,
        comment="MCP服务器配置列表"
    )


class PromptTemplate(Base, TimestampMixin, DictMixin):
    """提示词模板模型

    存储可复用的提示词模板配置
    """

    __tablename__ = "prompt_template"

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        comment="模板ID"
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="模板名称"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="模板描述"
    )
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="模板分类 (basic_react, planning, validation, reflection等)"
    )
    template: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="模板内容"
    )
    variables: Mapped[Optional[Dict[str, str]]] = mapped_column(
        JSON,
        nullable=True,
        comment="模板变量字典"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否激活"
    )
    version: Mapped[str] = mapped_column(
        String(50),
        default="1.0",
        nullable=False,
        comment="版本号"
    )
    tags: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        comment="标签列表"
    )


class DecisionRule(Base, TimestampMixin, DictMixin):
    """决策规则模型

    存储用于决策的规则配置
    """

    __tablename__ = "decision_rule"

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        comment="规则ID"
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="规则名称"
    )
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="规则分类 (intent_analysis, todo_execution, validation等)"
    )
    condition: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="条件表达式"
    )
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="动作类型"
    )
    parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="参数配置"
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="优先级 (数值越大优先级越高)"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否激活"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="规则描述"
    )


class WorkflowConfig(Base, TimestampMixin, DictMixin):
    """流程配置模型

    存储工作流程的节点和连接配置
    """

    __tablename__ = "workflow_config"

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        comment="配置ID"
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="流程名称"
    )
    version: Mapped[str] = mapped_column(
        String(50),
        default="1.0",
        nullable=False,
        comment="版本号"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="流程描述"
    )
    max_steps: Mapped[int] = mapped_column(
        Integer,
        default=20,
        nullable=False,
        comment="最大步骤数"
    )
    nodes: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="节点配置"
    )
    connections: Mapped[Optional[List[Dict[str, str]]]] = mapped_column(
        JSON,
        nullable=True,
        comment="连接配置"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否激活"
    )
    intent_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="适用意图类型"
    )


class StreamingConfig(Base, TimestampMixin, DictMixin):
    """流式输出配置模型

    存储流式响应相关配置
    """

    __tablename__ = "streaming_config"

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        comment="配置ID"
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用流式输出"
    )
    streaming_types: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        comment="流式类型列表"
    )
    complete_types: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        comment="完整发送类型列表"
    )
    chunk_size: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="文本块大小"
    )
    buffer_size: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
        comment="缓冲区大小"
    )
    sse_queue_maxsize: Mapped[int] = mapped_column(
        Integer,
        default=100,
        nullable=False,
        comment="SSE队列最大长度"
    )
    sse_timeout: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
        comment="SSE队列超时(秒)"
    )


class ReActInstance(Base, TimestampMixin, DictMixin):
    """ReAct 实例模型

    存储ReAct实例的基本信息和运行配置
    """

    __tablename__ = "react_instance"

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        comment="实例ID"
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="实例名称"
    )
    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="实例代码"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="描述"
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="inactive",
        nullable=False,
        index=True,
        comment="状态: active/inactive/error"
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="是否启用"
    )

    max_iterations: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
        comment="最大迭代次数"
    )
    timeout: Mapped[int] = mapped_column(
        Integer,
        default=300,
        nullable=False,
        comment="超时时间(秒)"
    )

    enable_planning: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用规划阶段"
    )
    enable_validation: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用验证阶段"
    )
    enable_reflection: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用反思阶段"
    )
    enable_streaming: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否启用流式响应"
    )

    quality_threshold: Mapped[float] = mapped_column(
        Float,
        default=0.7,
        nullable=False,
        comment="质量阈值"
    )
    retry_attempts: Mapped[int] = mapped_column(
        Integer,
        default=3,
        nullable=False,
        comment="重试次数"
    )

    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="扩展元数据"
    )
    tags: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        comment="标签列表"
    )

    llm_config_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("llm_config.id", ondelete="CASCADE"),
        nullable=False,
        comment="LLM配置ID"
    )
    mcp_config_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        ForeignKey("mcp_config.id", ondelete="SET NULL"),
        nullable=True,
        comment="MCP配置ID"
    )
    rag_config_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        ForeignKey("rag_config.id", ondelete="SET NULL"),
        nullable=True,
        comment="RAG配置ID"
    )
    prompt_template_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        ForeignKey("prompt_template.id", ondelete="SET NULL"),
        nullable=True,
        comment="默认提示词模板ID"
    )
    decision_rule_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        ForeignKey("decision_rule.id", ondelete="SET NULL"),
        nullable=True,
        comment="决策规则ID"
    )
    workflow_config_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        ForeignKey("workflow_config.id", ondelete="SET NULL"),
        nullable=True,
        comment="流程配置ID"
    )
    streaming_config_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        ForeignKey("streaming_config.id", ondelete="SET NULL"),
        nullable=True,
        comment="流式输出配置ID"
    )

    async def to_prompt_config(self) -> Optional[Dict[str, Any]]:
        """转换为提示词配置格式

        :returns: 提示词配置字典或None
        """
        try:
            from react.config.prompt import (
                SystemPromptConfig,
                PlannerPromptConfig,
                ExecutorPromptConfig,
                PromptConfig
            )
            from init.msg.models import PromptConfigRequest

            prompt_config_id = self.prompt_template_id
            if not prompt_config_id:
                return None

            async with db.get_session() as session:
                stmt = select(PromptTemplate).where(PromptTemplate.id == prompt_config_id)
                result = await session.execute(stmt)
                template = result.scalar_one_or_none()

                if not template:
                    return None

                # 根据模板类别创建相应的配置
                if template.category == "system":
                    return {
                        "system": {
                            "template": template.template
                        }
                    }
                elif template.category == "planner":
                    variables = template.variables or {}
                    return {
                        "planner": {
                            "summary": variables.get("summary", ""),
                            "tools": variables.get("tools", ""),
                            "analysis": variables.get("analysis", ""),
                            "tool_name": variables.get("tool_name", "")
                        }
                    }
                elif template.category == "executor":
                    variables = template.variables or {}
                    return {
                        "executor": {
                            "tool_descriptions": variables.get("tool_descriptions", ""),
                            "planning_conclusion": variables.get("planning_conclusion", ""),
                            "tool_name": variables.get("tool_name", "")
                        }
                    }
                else:
                    return None
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"转换提示词配置失败: {e}", exc_info=True)
            return None

    async def from_prompt_config(self, prompt_config: Dict[str, Any]) -> None:
        """从提示词配置更新实例

        :param prompt_config: 提示词配置字典
        """
        try:
            async with db.get_session() as session:
                system_config = prompt_config.get("system")
                planner_config = prompt_config.get("planner")
                executor_config = prompt_config.get("executor")

                if system_config:
                    template_id = f"prompt_system_{self.id}"
                    template = PromptTemplate(
                        id=template_id,
                        name=f"system_prompt_{self.code}",
                        description="系统提示词模板",
                        category="system",
                        template=system_config.get("template", ""),
                        variables={},
                        is_active=True,
                        version="1.0",
                        tags=["system", "react"]
                    )
                    session.add(template)
                    self.prompt_template_id = template_id

                if planner_config:
                    template_id = f"prompt_planner_{self.id}"
                    template = PromptTemplate(
                        id=template_id,
                        name=f"planner_prompt_{self.code}",
                        description="规划阶段提示词模板",
                        category="planner",
                        template="",  # Planner使用变量而非模板
                        variables={
                            "summary": planner_config.get("summary", ""),
                            "tools": planner_config.get("tools", ""),
                            "analysis": planner_config.get("analysis", ""),
                            "tool_name": planner_config.get("tool_name", "")
                        },
                        is_active=True,
                        version="1.0",
                        tags=["planner", "react"]
                    )
                    session.add(template)
                    self.prompt_template_id = template_id

                if executor_config:
                    template_id = f"prompt_executor_{self.id}"
                    template = PromptTemplate(
                        id=template_id,
                        name=f"executor_prompt_{self.code}",
                        description="执行阶段提示词模板",
                        category="executor",
                        template="",  # Executor使用变量而非模板
                        variables={
                            "tool_descriptions": executor_config.get("tool_descriptions", ""),
                            "planning_conclusion": executor_config.get("planning_conclusion", ""),
                            "tool_name": executor_config.get("tool_name", "")
                        },
                        is_active=True,
                        version="1.0",
                        tags=["executor", "react"]
                    )
                    session.add(template)
                    self.prompt_template_id = template_id

                await session.commit()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"更新提示词配置失败: {e}", exc_info=True)
            raise

    async def to_meta_react_config(self) -> Dict[str, Any]:
        """转换为 Meta-ReAct 配置格式

        :returns: 配置字典
        """
        from sqlalchemy.ext.asyncio import AsyncSession
        from init.db import db
        import asyncio
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"[to_meta_react_config] 开始转换实例: {self.id}, llm_config_id={self.llm_config_id}")

        config = {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "status": self.status,
            "is_enabled": self.is_enabled,
            "max_iterations": self.max_iterations,
            "timeout": self.timeout,
            "meta_react": {
                "enable_planning": self.enable_planning,
                "enable_validation": self.enable_validation,
                "enable_reflection": self.enable_reflection,
                "enable_streaming": self.enable_streaming,
                "quality_threshold": self.quality_threshold,
                "retry_attempts": self.retry_attempts
            },
            "extra_metadata": self.extra_metadata,
            "tags": self.tags
        }

        # 同步查询相关配置
        try:
            # 始终执行配置查询，不检查事件循环状态
            logger.info(f"[to_meta_react_config] 开始执行配置查询")
            try:
                loop = asyncio.get_event_loop()
                logger.info(f"[to_meta_react_config] 事件循环状态: running={loop.is_running()}")
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                logger.info(f"[to_meta_react_config] 创建新事件循环")

        except Exception as e:
            logger.error(f"[to_meta_react_config] 事件循环初始化失败: {e}")

        # 同步方式查询配置
        try:
            async def _load_configs():
                logger.info(f"[to_meta_react_config] 开始异步查询配置")
                async with db.get_session() as session:
                    # 查询 LLM 配置
                    llm_config = {}
                    if self.llm_config_id:
                        logger.info(f"[to_meta_react_config] 查询 LLMConfig: {self.llm_config_id}")
                        llm_stmt = select(LLMConfig).where(LLMConfig.id == self.llm_config_id)
                        llm_result = await session.execute(llm_stmt)
                        llm = llm_result.scalar_one_or_none()
                        if llm:
                            llm_config = {
                                "provider": llm.provider,
                                "model": llm.model,
                                "api_key": llm.api_key,
                                "base_url": llm.base_url,
                                "temperature": llm.temperature,
                                "max_tokens": llm.max_tokens
                            }
                            logger.info(f"[to_meta_react_config] LLMConfig查询成功: base_url={llm.base_url}")
                        else:
                            logger.error(f"[to_meta_react_config] LLMConfig不存在: {self.llm_config_id}")

                    # 查询 MCP 配置
                    mcp_config = {}
                    if self.mcp_config_id:
                        mcp_stmt = select(MCPConfig).where(MCPConfig.id == self.mcp_config_id)
                        mcp_result = await session.execute(mcp_stmt)
                        mcp = mcp_result.scalar_one_or_none()
                        if mcp:
                            # mcp.servers 是 JSON 数组，存储为字典
                            servers_list = mcp.servers or []
                            servers = []
                            for s in servers_list:
                                if isinstance(s, dict):
                                    servers.append({
                                        "name": s.get("name", ""),
                                        "type": s.get("type", ""),
                                        "command": s.get("command", None),
                                        "url": s.get("url", None),
                                        "args": s.get("args", []),
                                        "headers": s.get("headers", None),
                                        "auth_token": s.get("auth_token", None),
                                        "timeout": s.get("timeout", None),
                                        "reconnect_attempts": s.get("reconnect_attempts", None)
                                    })
                                else:
                                    # 如果不是字典，尝试转换为字典
                                    servers.append({
                                        "name": getattr(s, "name", ""),
                                        "type": getattr(s, "type", ""),
                                        "command": getattr(s, "command", None),
                                        "url": getattr(s, "url", None),
                                        "args": getattr(s, "args", []),
                                        "headers": getattr(s, "headers", None),
                                        "auth_token": getattr(s, "auth_token", None),
                                        "timeout": getattr(s, "timeout", None),
                                        "reconnect_attempts": getattr(s, "reconnect_attempts", None)
                                    })

                            mcp_config = {
                                "connection_timeout": mcp.connection_timeout,
                                "reconnect_attempts": mcp.reconnect_attempts,
                                "servers": servers
                            }

                    # 查询 RAG 配置
                    rag_config = {}
                    if self.rag_config_id:
                        rag_stmt = select(RAGConfig).where(RAGConfig.id == self.rag_config_id)
                        rag_result = await session.execute(rag_stmt)
                        rag = rag_result.scalar_one_or_none()
                        if rag:
                            rag_config = {
                                "enabled": rag.enabled,
                                "endpoint": rag.endpoint,
                                "api_key": rag.api_key,
                                "top_k": rag.top_k,
                                "score_threshold": rag.score_threshold
                            }

                    return {
                        "llm": llm_config,
                        "mcp": mcp_config,
                        "rag": rag_config
                    }

            # 直接在新事件循环中执行异步查询
            logger.info(f"[to_meta_react_config] 开始执行异步查询")
            configs = await _load_configs()
            logger.info(f"[to_meta_react_config] 异步查询完成，配置: {configs}")
            config.update(configs)
        except Exception as e:
            # 如果查询失败，记录日志但不中断
            logger.error(f"[to_meta_react_config] 查询 ReActInstance 配置失败: {e}", exc_info=True)

        logger.info(f"[to_meta_react_config] 返回配置完成")
        return config


class RAGConfig(Base, TimestampMixin, DictMixin):
    """RAG 配置模型

    存储检索增强生成相关配置
    """

    __tablename__ = "rag_config"

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        comment="配置ID"
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否启用RAG"
    )
    endpoint: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="RAG服务终端地址"
    )
    api_key: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="API密钥"
    )
    top_k: Mapped[int] = mapped_column(
        Integer,
        default=5,
        nullable=False,
        comment="检索文档数量"
    )
    score_threshold: Mapped[float] = mapped_column(
        Float,
        default=0.7,
        nullable=False,
        comment="相似度阈值"
    )


class ExecutionRecord(Base, TimestampMixin, DictMixin):
    """执行记录模型

    存储Meta-ReAct执行历史记录
    """

    __tablename__ = "execution_record"

    id: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
        comment="记录ID"
    )
    instance_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("react_instance.id", ondelete="CASCADE"),
        nullable=False,
        comment="实例ID"
    )
    session_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="会话ID"
    )
    query: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="用户查询"
    )
    response: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="响应内容"
    )
    execution_time: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="执行时间(秒)"
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="执行状态"
    )
    quality_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="质量分数"
    )
    tools_used: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        comment="使用的工具列表"
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="错误信息"
    )
    extra_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="元数据"
    )
