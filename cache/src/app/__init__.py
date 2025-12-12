from fastapi import FastAPI
from contextlib import asynccontextmanager

from init.db import (
    db,
    redis_manager,
    minio_manager,
    vllm_manager,
)
from init.vector import qdrant_manager, embedding_manager
from init.db.redis.stream import init_stream_queue_manager
from init.config import (
    init_settings,
    DatabaseConfig,
    RedisConfig,
    StorageConfig,
    QdrantConfig,
    EmbeddingConfig,
    ServerConfig,
    LLMConfig,
)
from init.config.container.loader import load_from_toml


def setup_routes(app: FastAPI, base_url: str) -> None:
    settings = init_settings()
    server_config = ServerConfig.load_from_settings(settings=settings)

    # swagger routes
    from .swagger import register_swagger_routes
    register_swagger_routes(
        app,
        static_path=server_config.static_path,
        base_url=server_config.base_url
    )

    # subapp routes
    # from app.score.route import router as score_router
    # app.include_router(score_router, prefix=base_url)


# MCP lifespan manager
@asynccontextmanager
async def mcp_lifespan(app: FastAPI):
    """Manage MCP session manager lifecycle"""
    from .cmcp import mcp
    async with mcp.session_manager.run():
        yield


async def create_app(debug: bool = False) -> FastAPI:
    settings = init_settings()
    server_config = ServerConfig.load_from_settings(settings=settings)

    app = FastAPI(
        title="Document Upload Service",
        description="Document upload/manage/analysis service API",
        version="0.1.0",
        debug=debug,
        openapi_url=server_config.base_url + '/openapi.json',
        lifespan=mcp_lifespan,
    )
    # about mcp
    from .cmcp import mcp, setup_tools
    setup_tools()
    app.mount(
        server_config.base_url + '/mcp',
        app=mcp.streamable_http_app()
    )

    # Initialize database and cache managers
    redis_config = RedisConfig.load_from_settings(settings=settings)
    await redis_manager.init(**redis_config.as_dict())

    # Initialize MinIO storage manager
    storage_config = StorageConfig.load_from_settings(settings=settings)
    await minio_manager.init(
        endpoint=storage_config.endpoint,
        access_key=storage_config.access_key,
        secret_key=storage_config.secret_key,
        region=storage_config.region or 'us-east-1',
        secure=storage_config.secure,
    )

    # Initialize Qdrant manager
    qdrant_config = QdrantConfig.load_from_settings(settings=settings)
    await qdrant_manager.init(
        host=qdrant_config.host,
        port=qdrant_config.port,
        grpc_port=qdrant_config.grpc_port,
        api_key=qdrant_config.api_key,
        timeout=qdrant_config.timeout,
        prefer_grpc=qdrant_config.prefer_grpc,
    )

    # Initialize Embedding manager
    embedding_config = EmbeddingConfig.load_from_settings(settings=settings)
    await embedding_manager.init(
        base_url=embedding_config.base_url,
        model_name=embedding_config.model_name,
        embedding_dim=embedding_config.embedding_dim,
        timeout=embedding_config.timeout,
        max_concurrent=embedding_config.max_concurrent,
    )

    # Initialize vLLM client manager
    llm_config = LLMConfig.load_from_settings(settings=settings)
    vllm_manager.init(
        base_url=llm_config.base_url,
        default_model=llm_config.default_model,
        api_key=llm_config.api_key,
        default_max_tokens=llm_config.default_max_tokens,
        default_temperature=llm_config.default_temperature,
        default_top_p=llm_config.default_top_p,
    )

    # Initialize additional LLM clients from TOML config if provided
    toml_settings = load_from_toml(server_config.config_file)
    if hasattr(toml_settings, 'llm'):
        for llm_name, llm_data in toml_settings.vllm.items():
            vllm_manager.init_client(
                code=llm_name,
                base_url=llm_data.base_url,
                default_model=llm_data.default_model,
                api_key=llm_data.api_key,
                default_max_tokens=llm_data.default_max_tokens,
                default_temperature=llm_data.default_temperature,
                default_top_p=llm_data.default_top_p,
                set_as_default=False,
            )

    setup_routes(app, base_url=server_config.base_url)
    return app
