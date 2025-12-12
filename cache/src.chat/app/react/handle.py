"""
ReAct Instance Handler

Provides CRUD operations and status management for ReAct instances
Based on new ORM models (react_instance, llm_config, mcp_config, rag_config)
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from structure.models import (
    ReActInstance,
    LLMConfig,
    MCPConfig,
    RAGConfig
)
from init.msg.models import (
    ReActCreateRequest,
    ReActUpdateRequest,
    ReActConfigUpdateRequest,
    ReActStatusUpdateRequest,
    ReActPromptUpdateRequest,
)
from init.db import db

logger = logging.getLogger(__name__)


class ReActHandler:
    """ReAct instance handler"""

    def __init__(self, db_session: AsyncSession):
        """
        Initialize handler

        :param db_session: Database session
        """
        self.db = db_session

    async def create_react_instance(
        self,
        request: ReActCreateRequest
    ) -> Dict[str, Any]:
        """
        Create ReAct instance

        :param request: Create request
        :return: Created instance information
        """
        instance_id = await self._generate_instance_id(request)
        llm_config_id = f"llm_{instance_id}"
        mcp_config_id = f"mcp_{instance_id}"
        rag_config_id = f"rag_{instance_id}"

        llm_config = await self._create_llm_config(
            request=request,
            config_id=llm_config_id
        )
        self.db.add(llm_config)

        mcp_config = await self._create_mcp_config(
            request=request,
            config_id=mcp_config_id
        )
        self.db.add(mcp_config)

        rag_config = await self._create_rag_config(
            request=request,
            config_id=rag_config_id
        )
        self.db.add(rag_config)

        instance = await self._create_react_instance_model(
            request=request,
            instance_id=instance_id,
            llm_config_id=llm_config_id,
            mcp_config_id=mcp_config_id,
            rag_config_id=rag_config_id
        )
        self.db.add(instance)

        await self.db.commit()
        await self.db.refresh(instance)

        logger.info(f"ReAct instance created successfully: {instance_id}")
        result = await self._instance_to_dict(instance)
        return result

    async def _generate_instance_id(self, request: ReActCreateRequest) -> str:
        """
        Generate instance ID

        :param request: Create request
        :return: Instance ID
        """
        return request.id or f"react_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

    async def _create_llm_config(
        self,
        request: ReActCreateRequest,
        config_id: str
    ) -> LLMConfig:
        """
        Create LLM configuration

        :param request: Create request
        :param config_id: Configuration ID
        :return: LLM configuration object
        """
        return LLMConfig(
            id=config_id,
            provider=request.llm_provider,
            model=request.llm_model,
            api_key=request.llm_api_key,
            base_url=request.llm_base_url,
            temperature=request.llm_temperature,
            max_tokens=request.llm_max_tokens,
            timeout=request.llm_timeout,
            max_retries=request.llm_max_retries
        )

    async def _create_mcp_config(
        self,
        request: ReActCreateRequest,
        config_id: str
    ) -> MCPConfig:
        """
        Create MCP configuration

        :param request: Create request
        :param config_id: Configuration ID
        :return: MCP configuration object
        """
        return MCPConfig(
            id=config_id,
            enabled=request.mcp_enabled,
            servers=request.mcp_servers
        )

    async def _create_rag_config(
        self,
        request: ReActCreateRequest,
        config_id: str
    ) -> RAGConfig:
        """
        Create RAG configuration

        :param request: Create request
        :param config_id: Configuration ID
        :return: RAG configuration object
        """
        return RAGConfig(
            id=config_id,
            enabled=request.rag_enabled,
            endpoint=request.rag_endpoint,
            api_key=request.rag_api_key,
            top_k=request.rag_top_k,
            score_threshold=request.rag_score_threshold
        )

    async def _create_react_instance_model(
        self,
        request: ReActCreateRequest,
        instance_id: str,
        llm_config_id: str,
        mcp_config_id: str,
        rag_config_id: str
    ) -> ReActInstance:
        """
        Create ReAct instance model

        :param request: Create request
        :param instance_id: Instance ID
        :param llm_config_id: LLM configuration ID
        :param mcp_config_id: MCP configuration ID
        :param rag_config_id: RAG configuration ID
        :return: ReAct instance object
        """
        return ReActInstance(
            id=instance_id,
            name=request.name,
            code=request.code,
            description=request.description,
            status="inactive",
            is_enabled=True,
            max_iterations=request.max_iterations,
            timeout=request.timeout,
            enable_streaming=request.enable_streaming,
            extra_metadata=request.metadata,
            tags=request.tags,
            llm_config_id=llm_config_id,
            mcp_config_id=mcp_config_id,
            rag_config_id=rag_config_id
        )

    async def get_react_instance(
        self,
        instance_id: str
    ) -> Dict[str, Any]:
        """
        Get ReAct instance details

        :param instance_id: Instance ID
        :return: Instance detailed information
        """
        result = await self.db.execute(
            select(ReActInstance)
            .where(ReActInstance.id == instance_id)
        )
        instance = result.scalar_one_or_none()

        if not instance:
            raise HTTPException(
                status_code=404,
                detail=f"Instance not found: {instance_id}"
            )

        return await self._instance_to_dict(instance)

    async def list_react_instances(
        self,
        limit: int = 20,
        offset: int = 0,
        status: Optional[str] = None,
        is_enabled: Optional[bool] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get ReAct instance list

        :param limit: Limit count
        :param offset: Offset
        :param status: Status filter
        :param is_enabled: Is enabled filter
        :param search: Search keyword
        :return: Instance list
        """
        query = self._build_list_query(
            status=status,
            is_enabled=is_enabled,
            search=search
        )
        total = await self._get_total_count(query)
        query = query.offset(offset).limit(limit)
        instances = await self._execute_list_query(query)
        items = await self._convert_instances_to_dict(instances)

        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "items": items
        }

    def _build_list_query(
        self,
        status: Optional[str],
        is_enabled: Optional[bool],
        search: Optional[str]
    ) -> Any:
        """
        Build list query

        :param status: Status filter
        :param is_enabled: Is enabled filter
        :param search: Search keyword
        :return: Query object
        """
        query = select(ReActInstance)

        if status:
            query = query.where(ReActInstance.status == status)

        if is_enabled is not None:
            query = query.where(ReActInstance.is_enabled == is_enabled)

        if search:
            query = query.where(
                ReActInstance.name.ilike(f"%{search}%") |
                ReActInstance.code.ilike(f"%{search}%")
            )

        return query

    async def _get_total_count(self, query: Any) -> int:
        """
        Get total count

        :param query: Query object
        :return: Total count
        """
        from sqlalchemy import func, select as sql_select

        count_result = await self.db.execute(
            sql_select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar()
        return total if total is not None else 0

    async def _execute_list_query(self, query: Any) -> List[ReActInstance]:
        """
        Execute list query

        :param query: Query object
        :return: Instance list
        """
        result = await self.db.execute(query)
        instances = result.scalars().all()
        return list(instances) if instances else []

    async def _convert_instances_to_dict(
        self,
        instances: List[ReActInstance]
    ) -> List[Dict[str, Any]]:
        """
        Convert instance list to dictionary

        :param instances: Instance list
        :return: Dictionary list
        """
        items = []
        for inst in instances:
            items.append(await self._instance_to_dict(inst))
        return items

    async def update_react_instance(
        self,
        instance_id: str,
        request: ReActUpdateRequest
    ) -> Dict[str, Any]:
        """
        Update ReAct instance

        :param instance_id: Instance ID
        :param request: Update request
        :return: Updated instance information
        """
        instance = await self._get_instance_by_id(instance_id)

        await self._update_instance_fields(instance, request)

        if instance.llm_config_id:
            await self._update_llm_config(
                instance_id=instance.llm_config_id,
                request=request
            )

        if instance.mcp_config_id:
            await self._update_mcp_config(
                instance_id=instance.mcp_config_id,
                request=request
            )

        if instance.rag_config_id:
            await self._update_rag_config(
                instance_id=instance.rag_config_id,
                request=request
            )

        await self.db.commit()
        await self.db.refresh(instance)

        logger.info(f"ReAct instance updated successfully: {instance_id}")
        return await self._instance_to_dict(instance)

    async def _get_instance_by_id(self, instance_id: str) -> ReActInstance:
        """
        Get instance by ID

        :param instance_id: Instance ID
        :return: ReAct instance
        """
        result = await self.db.execute(
            select(ReActInstance)
            .where(ReActInstance.id == instance_id)
        )
        instance = result.scalar_one_or_none()

        if not instance:
            raise HTTPException(
                status_code=404,
                detail=f"Instance not found: {instance_id}"
            )

        return instance

    async def _update_instance_fields(
        self,
        instance: ReActInstance,
        request: ReActUpdateRequest
    ) -> None:
        """
        Update instance fields

        :param instance: ReAct instance
        :param request: Update request
        """
        if request.name is not None:
            instance.name = request.name
        if request.code is not None:
            instance.code = request.code
        if request.description is not None:
            instance.description = request.description
        if request.status is not None:
            instance.status = request.status
        if request.is_enabled is not None:
            instance.is_enabled = request.is_enabled
        if request.max_iterations is not None:
            instance.max_iterations = request.max_iterations
        if request.timeout is not None:
            instance.timeout = request.timeout
        if request.enable_streaming is not None:
            instance.enable_streaming = request.enable_streaming
        if request.metadata is not None:
            instance.extra_metadata = request.metadata
        if request.tags is not None:
            instance.tags = request.tags

    async def _update_llm_config(
        self,
        instance_id: str,
        request: ReActUpdateRequest
    ) -> None:
        """
        Update LLM configuration

        :param instance_id: LLM configuration ID
        :param request: Update request
        """
        llm_result = await self.db.execute(
            select(LLMConfig).where(LLMConfig.id == instance_id)
        )
        llm_config = llm_result.scalar_one_or_none()
        if llm_config:
            if request.llm_provider is not None:
                llm_config.provider = request.llm_provider
            if request.llm_model is not None:
                llm_config.model = request.llm_model
            if request.llm_api_key is not None:
                llm_config.api_key = request.llm_api_key
            if request.llm_base_url is not None:
                llm_config.base_url = request.llm_base_url
            if request.llm_temperature is not None:
                llm_config.temperature = request.llm_temperature
            if request.llm_max_tokens is not None:
                llm_config.max_tokens = request.llm_max_tokens
            if request.llm_timeout is not None:
                llm_config.timeout = request.llm_timeout
            if request.llm_max_retries is not None:
                llm_config.max_retries = request.llm_max_retries

    async def _update_mcp_config(
        self,
        instance_id: str,
        request: ReActUpdateRequest
    ) -> None:
        """
        Update MCP configuration

        :param instance_id: MCP configuration ID
        :param request: Update request
        """
        mcp_result = await self.db.execute(
            select(MCPConfig).where(MCPConfig.id == instance_id)
        )
        mcp_config = mcp_result.scalar_one_or_none()
        if mcp_config:
            if request.mcp_enabled is not None:
                mcp_config.enabled = request.mcp_enabled
            if request.mcp_servers is not None:
                mcp_config.servers = request.mcp_servers

    async def _update_rag_config(
        self,
        instance_id: str,
        request: ReActUpdateRequest
    ) -> None:
        """
        Update RAG configuration

        :param instance_id: RAG configuration ID
        :param request: Update request
        """
        rag_result = await self.db.execute(
            select(RAGConfig).where(RAGConfig.id == instance_id)
        )
        rag_config = rag_result.scalar_one_or_none()
        if rag_config:
            if request.rag_enabled is not None:
                rag_config.enabled = request.rag_enabled
            if request.rag_endpoint is not None:
                rag_config.endpoint = request.rag_endpoint
            if request.rag_api_key is not None:
                rag_config.api_key = request.rag_api_key
            if request.rag_top_k is not None:
                rag_config.top_k = request.rag_top_k
            if request.rag_score_threshold is not None:
                rag_config.score_threshold = request.rag_score_threshold

    async def delete_react_instance(
        self,
        instance_id: str
    ) -> Dict[str, Any]:
        """
        Delete ReAct instance (soft delete)

        :param instance_id: Instance ID
        :return: Delete result
        """
        result = await self.db.execute(
            select(ReActInstance).where(ReActInstance.id == instance_id)
        )
        instance = result.scalar_one_or_none()

        if not instance:
            raise HTTPException(
                status_code=404,
                detail=f"Instance not found: {instance_id}"
            )

        instance.is_enabled = False
        instance.status = "inactive"

        await self.db.commit()

        logger.info(f"ReAct instance deleted successfully: {instance_id}")
        return {
            "id": instance_id,
            "status": "deleted",
            "message": "Instance has been disabled"
        }

    async def update_react_config(
        self,
        instance_id: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update ReAct configuration

        :param instance_id: Instance ID
        :param config: Configuration dictionary
        :return: Updated instance information
        """
        result = await self.db.execute(
            select(ReActInstance)
            .where(ReActInstance.id == instance_id)
        )
        instance = result.scalar_one_or_none()

        if not instance:
            raise HTTPException(
                status_code=404,
                detail=f"Instance not found: {instance_id}"
            )

        instance.extra_metadata = config
        await self.db.commit()
        await self.db.refresh(instance)

        logger.info(f"ReAct configuration updated successfully: {instance_id}")
        return await self._instance_to_dict(instance)

    async def get_react_config(
        self,
        instance_id: str
    ) -> Dict[str, Any]:
        """
        Get ReAct configuration

        :param instance_id: Instance ID
        :return: Configuration information
        """
        result = await self.db.execute(
            select(ReActInstance)
            .where(ReActInstance.id == instance_id)
        )
        instance = result.scalar_one_or_none()

        if not instance:
            raise HTTPException(
                status_code=404,
                detail=f"Instance not found: {instance_id}"
            )

        return await instance.to_meta_react_config()

    async def update_react_status(
        self,
        instance_id: str,
        status: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update ReAct status

        :param instance_id: Instance ID
        :param status: Status
        :param reason: Status change reason
        :return: Updated instance information
        """
        result = await self.db.execute(
            select(ReActInstance)
            .where(ReActInstance.id == instance_id)
        )
        instance = result.scalar_one_or_none()

        if not instance:
            raise HTTPException(
                status_code=404,
                detail=f"Instance not found: {instance_id}"
            )

        instance.status = status
        if reason:
            if instance.extra_metadata is None:
                instance.extra_metadata = {}
            instance.extra_metadata["status_reason"] = reason
            instance.extra_metadata["status_updated_at"] = datetime.now().isoformat()

        await self.db.commit()
        await self.db.refresh(instance)

        logger.info(
            f"ReAct status updated successfully: {instance_id}, status={status}"
        )
        return await self._instance_to_dict(instance)

    async def get_active_instances(self) -> List[Dict[str, Any]]:
        """
        Get all active instances

        :return: Active instance list
        """
        result = await self.db.execute(
            select(ReActInstance)
            .where(
                ReActInstance.status == "active",
                ReActInstance.is_enabled == True
            )
        )
        instances = result.scalars().all()

        items = []
        for inst in instances:
            items.append(await self._instance_to_dict(inst))
        return items

    async def activate_react_instance(self, instance_id: str) -> Dict[str, Any]:
        """
        Activate ReAct instance

        :param instance_id: Instance ID
        :return: Activated instance information
        """
        instance = await self._get_instance_by_id(instance_id)

        from react.manager import react_manager

        llm_config_obj = await self._get_llm_config(instance.llm_config_id)
        mcp_config_obj = await self._get_mcp_config(instance.mcp_config_id) if instance.mcp_config_id else None

        if llm_config_obj and mcp_config_obj:
            llm_config = await self._build_llm_config(llm_config_obj)
            mcp_config = await self._build_mcp_config(mcp_config_obj)

            await react_manager.create_instance(
                instance_id,
                llm_config,
                mcp_config
            )

        await self.db.refresh(instance)

        logger.info(f"ReAct instance activated successfully: {instance_id}")
        return await self._instance_to_dict(instance)

    async def _get_llm_config(self, config_id: str) -> Optional[LLMConfig]:
        """
        Get LLM configuration

        :param config_id: Configuration ID
        :return: LLM configuration object
        """
        if not config_id:
            return None

        llm_result = await self.db.execute(
            select(LLMConfig).where(LLMConfig.id == config_id)
        )
        return llm_result.scalar_one_or_none()

    async def _get_mcp_config(self, config_id: str) -> Optional[MCPConfig]:
        """
        Get MCP configuration

        :param config_id: Configuration ID
        :return: MCP configuration object
        """
        if not config_id:
            return None

        mcp_result = await self.db.execute(
            select(MCPConfig).where(MCPConfig.id == config_id)
        )
        return mcp_result.scalar_one_or_none()

    async def _build_llm_config(self, llm_config_obj: LLMConfig) -> Any:
        """
        Build LLM configuration

        :param llm_config_obj: LLM configuration object
        :return: ReAct LLM configuration
        """
        from react.config.llm import LLMConfig as ReActLLMConfig

        return ReActLLMConfig(
            provider=llm_config_obj.provider,
            model=llm_config_obj.model,
            api_key=llm_config_obj.api_key or "",
            base_url=llm_config_obj.base_url,
            temperature=llm_config_obj.temperature,
            max_tokens=llm_config_obj.max_tokens
        )

    async def _build_mcp_config(self, mcp_config_obj: MCPConfig) -> Any:
        """
        Build MCP configuration

        :param mcp_config_obj: MCP configuration object
        :return: ReAct MCP configuration
        """
        from react.config.mcp import MCPConfig as ReActMCPConfig

        mcp_servers = []
        if mcp_config_obj.servers:
            for server in mcp_config_obj.servers:
                mcp_servers.append(
                    ReActMCPConfig.Server(
                        name=server["name"],
                        type=server.get("type", "stdio"),
                        command=server.get("command", "python"),
                        args=server.get("args", []),
                        headers=server.get("headers"),
                        auth_token=server.get("auth_token"),
                        timeout=server.get("timeout", 30),
                        reconnect_attempts=server.get("reconnect_attempts", 3)
                    )
                )

        return ReActMCPConfig(servers=mcp_servers)

    async def update_react_prompts(
        self,
        instance_id: str,
        request: ReActPromptUpdateRequest
    ) -> Dict[str, Any]:
        """
        Update ReAct prompt configuration

        :param instance_id: Instance ID
        :param request: Prompt configuration update request
        :return: Updated instance information
        """
        instance = await self._get_instance_by_id(instance_id)

        prompt_config_dict = request.prompts.as_dict()

        if request.validation_enabled:
            await self._validate_prompt_config(prompt_config_dict)

        await instance.from_prompt_config(prompt_config_dict)
        await self.db.commit()
        await self.db.refresh(instance)

        logger.info(f"ReAct prompt configuration updated successfully: {instance_id}")
        return await self._instance_to_dict(instance)

    async def _validate_prompt_config(
        self,
        prompt_config_dict: Dict[str, Any]
    ) -> None:
        """
        Validate prompt configuration

        :param prompt_config_dict: Prompt configuration dictionary
        :raises HTTPException: Raised when validation fails
        """
        from react.config.prompt import (
            SystemPromptConfig,
            PlannerPromptConfig,
            ExecutorPromptConfig
        )

        validation_errors = []

        if prompt_config_dict.get("system"):
            try:
                SystemPromptConfig()
            except TypeError as e:
                validation_errors.append(f"SystemPrompt: {str(e)}")

        if prompt_config_dict.get("planner"):
            try:
                PlannerPromptConfig(
                    summary=prompt_config_dict["planner"].get("summary", ""),
                    tools=prompt_config_dict["planner"].get("tools", ""),
                    analysis=prompt_config_dict["planner"].get("analysis", ""),
                    tool_name=prompt_config_dict["planner"].get("tool_name", "")
                )
            except TypeError as e:
                validation_errors.append(f"PlannerPrompt: {str(e)}")

        if prompt_config_dict.get("executor"):
            try:
                ExecutorPromptConfig(
                    tool_descriptions=prompt_config_dict["executor"].get("tool_descriptions", ""),
                    planning_conclusion=prompt_config_dict["executor"].get("planning_conclusion", ""),
                    tool_name=prompt_config_dict["executor"].get("tool_name", "")
                )
            except TypeError as e:
                validation_errors.append(f"ExecutorPrompt: {str(e)}")

        if validation_errors:
            raise HTTPException(
                status_code=400,
                detail=f"Prompt configuration validation failed: {'; '.join(validation_errors)}"
            )

    async def get_react_prompts(
        self,
        instance_id: str
    ) -> Dict[str, Any]:
        """
        Get ReAct prompt configuration

        :param instance_id: Instance ID
        :return: Prompt configuration information
        """
        result = await self.db.execute(
            select(ReActInstance)
            .where(ReActInstance.id == instance_id)
        )
        instance = result.scalar_one_or_none()

        if not instance:
            raise HTTPException(
                status_code=404,
                detail=f"Instance not found: {instance_id}"
            )

        result = await instance.to_prompt_config()
        if result is None:
            return {}
        return result

    async def validate_react_prompts(
        self,
        instance_id: str
    ) -> Dict[str, Any]:
        """
        Validate ReAct prompt configuration

        :param instance_id: Instance ID
        :return: Validation result
        """
        result = await self.db.execute(
            select(ReActInstance)
            .where(ReActInstance.id == instance_id)
        )
        instance = result.scalar_one_or_none()

        if not instance:
            raise HTTPException(
                status_code=404,
                detail=f"Instance not found: {instance_id}"
            )

        from react.config.prompt import (
            SystemPromptConfig,
            PlannerPromptConfig,
            ExecutorPromptConfig
        )

        validation_report = {
            "instance_id": instance_id,
            "all_valid": True,
            "results": {}
        }

        try:
            validation_report["results"]["system"] = SystemPromptConfig.get_validation_report()
        except Exception as e:
            validation_report["results"]["system"] = {
                "is_valid": False,
                "errors": [str(e)]
            }

        try:
            validation_report["results"]["planner"] = PlannerPromptConfig.get_validation_report()
        except Exception as e:
            validation_report["results"]["planner"] = {
                "is_valid": False,
                "errors": [str(e)]
            }

        try:
            validation_report["results"]["executor"] = ExecutorPromptConfig.get_validation_report()
        except Exception as e:
            validation_report["results"]["executor"] = {
                "is_valid": False,
                "errors": [str(e)]
            }

        validation_report["all_valid"] = all(
            r["is_valid"] for r in validation_report["results"].values()
        )

        return validation_report

    async def deactivate_react_instance(self, instance_id: str) -> Dict[str, Any]:
        """
        Deactivate ReAct instance

        :param instance_id: Instance ID
        :return: Deactivated instance information
        """
        result = await self.db.execute(
            select(ReActInstance)
            .where(ReActInstance.id == instance_id)
        )
        instance = result.scalar_one_or_none()

        if not instance:
            raise HTTPException(
                status_code=404,
                detail=f"Instance not found: {instance_id}"
            )

        from react.manager import react_manager
        await react_manager.destroy_instance(instance_id)

        instance.status = "inactive"
        await self.db.commit()
        await self.db.refresh(instance)

        logger.info(f"ReAct instance deactivated successfully: {instance_id}")
        return await self._instance_to_dict(instance)

    async def _instance_to_dict(self, instance: ReActInstance) -> Dict[str, Any]:
        """
        Convert instance to dictionary format

        :param instance: ReActInstance
        :return: Dictionary format instance information
        """
        result = await self._build_base_dict(instance)
        await self._populate_llm_config(result, instance)
        await self._populate_mcp_config(result, instance)
        await self._populate_rag_config(result, instance)

        return result

    async def _build_base_dict(self, instance: ReActInstance) -> Dict[str, Any]:
        """
        Build base dictionary

        :param instance: ReAct instance
        :return: Base dictionary
        """
        return {
            "id": instance.id,
            "name": instance.name,
            "code": instance.code,
            "description": instance.description,
            "status": instance.status,
            "is_enabled": instance.is_enabled,
            "max_iterations": instance.max_iterations,
            "timeout": instance.timeout,
            "enable_streaming": instance.enable_streaming,
            "metadata": instance.extra_metadata,
            "tags": instance.tags,
            "create_time": instance.create_time.isoformat() if instance.create_time else None,
            "update_time": instance.update_time.isoformat() if instance.update_time else None
        }

    async def _populate_llm_config(
        self,
        result: Dict[str, Any],
        instance: ReActInstance
    ) -> None:
        """
        Populate LLM configuration

        :param result: Result dictionary
        :param instance: ReAct instance
        """
        if not instance.llm_config_id:
            result.update({
                "llm_provider": None,
                "llm_model": None,
                "llm_api_key": None,
                "llm_base_url": None,
                "llm_temperature": None,
                "llm_max_tokens": None,
                "llm_timeout": None,
                "llm_max_retries": None
            })
            return

        llm_result = await self.db.execute(
            select(LLMConfig).where(LLMConfig.id == instance.llm_config_id)
        )
        llm_config = llm_result.scalar_one_or_none()
        if llm_config:
            result.update({
                "llm_provider": llm_config.provider,
                "llm_model": llm_config.model,
                "llm_api_key": llm_config.api_key,
                "llm_base_url": llm_config.base_url,
                "llm_temperature": llm_config.temperature,
                "llm_max_tokens": llm_config.max_tokens,
                "llm_timeout": llm_config.timeout,
                "llm_max_retries": llm_config.max_retries
            })
        else:
            result.update({
                "llm_provider": None,
                "llm_model": None,
                "llm_api_key": None,
                "llm_base_url": None,
                "llm_temperature": None,
                "llm_max_tokens": None,
                "llm_timeout": None,
                "llm_max_retries": None
            })

    async def _populate_mcp_config(
        self,
        result: Dict[str, Any],
        instance: ReActInstance
    ) -> None:
        """
        Populate MCP configuration

        :param result: Result dictionary
        :param instance: ReAct instance
        """
        if not instance.mcp_config_id:
            result.update({
                "mcp_enabled": False,
                "mcp_servers": None
            })
            return

        mcp_result = await self.db.execute(
            select(MCPConfig).where(MCPConfig.id == instance.mcp_config_id)
        )
        mcp_config = mcp_result.scalar_one_or_none()
        if mcp_config:
            result.update({
                "mcp_enabled": mcp_config.enabled,
                "mcp_servers": mcp_config.servers
            })
        else:
            result.update({
                "mcp_enabled": False,
                "mcp_servers": None
            })

    async def _populate_rag_config(
        self,
        result: Dict[str, Any],
        instance: ReActInstance
    ) -> None:
        """
        Populate RAG configuration

        :param result: Result dictionary
        :param instance: ReAct instance
        """
        if not instance.rag_config_id:
            result.update({
                "rag_enabled": False,
                "rag_endpoint": None,
                "rag_api_key": None,
                "rag_top_k": None,
                "rag_score_threshold": None
            })
            return

        rag_result = await self.db.execute(
            select(RAGConfig).where(RAGConfig.id == instance.rag_config_id)
        )
        rag_config = rag_result.scalar_one_or_none()
        if rag_config:
            result.update({
                "rag_enabled": rag_config.enabled,
                "rag_endpoint": rag_config.endpoint,
                "rag_api_key": rag_config.api_key,
                "rag_top_k": rag_config.top_k,
                "rag_score_threshold": rag_config.score_threshold
            })
        else:
            result.update({
                "rag_enabled": False,
                "rag_endpoint": None,
                "rag_api_key": None,
                "rag_top_k": None,
                "rag_score_threshold": None
            })


def get_react_handler(db_session) -> ReActHandler:
    """
    Get ReAct handler

    :param db_session: Database session
    :return: ReActHandler instance
    """
    return ReActHandler(db_session)


async def create_instance(request: ReActCreateRequest):
    """
    Create ReAct instance

    :param request: Create request
    :return: Created instance information
    """
    async with db.get_session() as session:
        handler = ReActHandler(session)
        result = await handler.create_react_instance(request)
        return result


async def get_instance(instance_id: str):
    """
    Get ReAct instance details

    :param instance_id: Instance ID
    :return: Instance detailed information
    """
    async with db.get_session() as session:
        handler = ReActHandler(session)
        result = await handler.get_react_instance(instance_id)
        return result


async def list_instances(
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None,
    is_enabled: Optional[bool] = None,
    search: Optional[str] = None
):
    """
    Get ReAct instance list

    :param limit: Limit count
    :param offset: Offset
    :param status: Status filter
    :param is_enabled: Is enabled filter
    :param search: Search keyword
    :return: Instance list
    """
    async with db.get_session() as session:
        handler = ReActHandler(session)
        result = await handler.list_react_instances(
            limit=limit,
            offset=offset,
            status=status,
            is_enabled=is_enabled,
            search=search
        )
        return result


async def update_instance(
    instance_id: str,
    request: ReActUpdateRequest
):
    """
    Update ReAct instance

    :param instance_id: Instance ID
    :param request: Update request
    :return: Updated instance information
    """
    async with db.get_session() as session:
        handler = ReActHandler(session)
        result = await handler.update_react_instance(instance_id, request)
        return result


async def delete_instance(instance_id: str):
    """
    Delete ReAct instance (soft delete)

    :param instance_id: Instance ID
    :return: Delete result
    """
    async with db.get_session() as session:
        handler = ReActHandler(session)
        result = await handler.delete_react_instance(instance_id)
        return result


async def update_config(
    instance_id: str,
    request: ReActConfigUpdateRequest
):
    """
    Update ReAct configuration

    :param instance_id: Instance ID
    :param request: Configuration update request
    :return: Updated instance information
    """
    async with db.get_session() as session:
        handler = ReActHandler(session)
        result = await handler.update_react_config(instance_id, request.config)
        return result


async def get_config(instance_id: str):
    """
    Get ReAct configuration

    :param instance_id: Instance ID
    :return: Configuration information
    """
    async with db.get_session() as session:
        handler = ReActHandler(session)
        result = await handler.get_react_config(instance_id)
        return result


async def update_status(
    instance_id: str,
    request: ReActStatusUpdateRequest
):
    """
    Update ReAct status

    :param instance_id: Instance ID
    :param request: Status update request
    :return: Updated instance information
    """
    async with db.get_session() as session:
        handler = ReActHandler(session)
        result = await handler.update_react_status(
            instance_id,
            request.status,
            request.reason
        )
        return result


async def get_active_instances():
    """
    Get all active instances

    :return: Active instance list
    """
    async with db.get_session() as session:
        handler = ReActHandler(session)
        result = await handler.get_active_instances()
        return result


async def activate_instance(instance_id: str):
    """
    Activate ReAct instance

    :param instance_id: Instance ID
    :return: Activated instance information
    """
    async with db.get_session() as session:
        handler = ReActHandler(session)
        result = await handler.activate_react_instance(instance_id)
        return result


async def deactivate_instance(instance_id: str):
    """
    Deactivate ReAct instance

    :param instance_id: Instance ID
    :return: Deactivated instance information
    """
    async with db.get_session() as session:
        handler = ReActHandler(session)
        result = await handler.deactivate_react_instance(instance_id)
        return result


async def update_prompts(
    instance_id: str,
    request: ReActPromptUpdateRequest
):
    """
    Update ReAct prompt configuration

    :param instance_id: Instance ID
    :param request: Prompt configuration update request
    :return: Updated instance information
    """
    async with db.get_session() as session:
        handler = ReActHandler(session)
        result = await handler.update_react_prompts(instance_id, request)
        return result


async def get_prompts(instance_id: str):
    """
    Get ReAct prompt configuration

    :param instance_id: Instance ID
    :return: Prompt configuration information
    """
    async with db.get_session() as session:
        handler = ReActHandler(session)
        result = await handler.get_react_prompts(instance_id)
        return result


async def validate_prompts(instance_id: str):
    """
    Validate ReAct prompt configuration

    :param instance_id: Instance ID
    :return: Validation result
    """
    async with db.get_session() as session:
        handler = ReActHandler(session)
        result = await handler.validate_react_prompts(instance_id)
        return result
