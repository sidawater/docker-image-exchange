"""
ReAct Routes

Provides API interfaces for ReAct instance management
"""

from fastapi import APIRouter

from init.msg.models import ReActOut
from .handle import (
    create_instance,
    get_instance,
    list_instances,
    update_instance,
    delete_instance,
    update_config,
    get_config,
    update_status,
    get_active_instances,
    activate_instance,
    deactivate_instance,
    update_prompts,
    get_prompts,
    validate_prompts
)

router = APIRouter(prefix="/react", tags=["react"])


router.add_api_route(
    path="/active",
    endpoint=get_active_instances,
    methods=["GET"],
    summary="Get active ReAct instances",
    description="Get all ReAct instances with active status and enabled"
)

router.add_api_route(
    path="/{instance_id}/activate",
    endpoint=activate_instance,
    methods=["POST"],
    response_model=ReActOut,
    summary="Activate ReAct instance",
    description="Activate the specified ReAct instance and initialize the corresponding ReAct Agent"
)

router.add_api_route(
    path="/{instance_id}/deactivate",
    endpoint=deactivate_instance,
    methods=["POST"],
    response_model=ReActOut,
    summary="Deactivate ReAct instance",
    description="Deactivate the specified ReAct instance and release corresponding resources"
)

router.add_api_route(
    path="/{instance_id}/config",
    endpoint=update_config,
    methods=["PUT"],
    summary="Update ReAct configuration",
    description="Update the configuration of the specified ReAct instance"
)

router.add_api_route(
    path="/{instance_id}/config",
    endpoint=get_config,
    methods=["GET"],
    summary="Get ReAct configuration",
    description="Get the configuration information of the specified ReAct instance"
)

router.add_api_route(
    path="/{instance_id}/status",
    endpoint=update_status,
    methods=["PUT"],
    summary="Update ReAct status",
    description="Update the status of the specified ReAct instance"
)

router.add_api_route(
    path="",
    endpoint=create_instance,
    methods=["POST"],
    response_model=ReActOut,
    summary="Create ReAct instance",
    description="Create a new ReAct instance"
)

router.add_api_route(
    path="",
    endpoint=list_instances,
    methods=["GET"],
    summary="Get ReAct instance list",
    description="Get a paginated list of ReAct instances with filtering and search support"
)

router.add_api_route(
    path="/{instance_id}",
    endpoint=get_instance,
    methods=["GET"],
    response_model=ReActOut,
    summary="Get ReAct instance details",
    description="Get detailed information of the specified ReAct instance"
)

router.add_api_route(
    path="/{instance_id}",
    endpoint=update_instance,
    methods=["PUT"],
    response_model=ReActOut,
    summary="Update ReAct instance",
    description="Update the information of the specified ReAct instance"
)

router.add_api_route(
    path="/{instance_id}",
    endpoint=delete_instance,
    methods=["DELETE"],
    summary="Delete ReAct instance",
    description="Delete the specified ReAct instance (soft delete)"
)

router.add_api_route(
    path="/{instance_id}/prompts",
    endpoint=update_prompts,
    methods=["PUT"],
    response_model=ReActOut,
    summary="Update ReAct prompt configuration",
    description="Update the prompt configuration of the specified ReAct instance, supporting custom system prompts, planning phase prompts, and execution phase prompts"
)

router.add_api_route(
    path="/{instance_id}/prompts",
    endpoint=get_prompts,
    methods=["GET"],
    summary="Get ReAct prompt configuration",
    description="Get the prompt configuration of the specified ReAct instance"
)

router.add_api_route(
    path="/{instance_id}/prompts/validate",
    endpoint=validate_prompts,
    methods=["GET"],
    summary="Validate ReAct prompt configuration",
    description="Validate the prompt configuration of the specified ReAct instance"
)
