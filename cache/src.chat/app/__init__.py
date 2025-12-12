from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from init.db import db, redis_manager, minio_manager
from init.db.redis.stream import init_stream_queue_manager
from init.config import (
    init_settings,
    DatabaseConfig,
    RedisConfig,
    StorageConfig,
    ServerConfig,
    ReActConfig,
)
from init.config.msg import MsgConfig
from init.msg import msg_manager
from .swagger import register_swagger_routes


def setup_routes(app: FastAPI, base_url: str) -> None:
    settings = init_settings()
    server_config = ServerConfig.load_from_settings(settings=settings)
    register_swagger_routes(
        app=app,
        static_path=server_config.static_path,
        base_url=server_config.base_url,
    )

    from app.chat.route import router as chat_router
    app.include_router(chat_router, prefix=base_url)

    from app.react.route import router as react_router
    app.include_router(react_router, prefix=base_url)


async def create_app(debug: bool = False) -> FastAPI:
    settings = init_settings()
    server_config = ServerConfig.load_from_settings(settings=settings)

    # Initialize database and cache managers
    db_config = DatabaseConfig.load_from_settings(settings=settings)
    db.init(**db_config.as_dict())
    redis_config = RedisConfig.load_from_settings(settings=settings)
    await redis_manager.init(**redis_config.as_dict())
    await init_stream_queue_manager(redis_manager)

    # Initialize MinIO storage manager
    storage_config = StorageConfig.load_from_settings(settings=settings)
    await minio_manager.init(
        endpoint=storage_config.endpoint,
        access_key=storage_config.access_key,
        secret_key=storage_config.secret_key,
        region=storage_config.region or 'us-east-1',
        secure=storage_config.secure,
    )

    # Initialize message service manager
    msg_config = MsgConfig.load_from_settings(settings=settings)
    msg_manager.init(
        base_url=msg_config.base_url,
        api_token=msg_config.api_token,
        timeout=msg_config.timeout,
    )

    # Initialize ReAct configuration
    react_config = ReActConfig.load_from_settings(settings=settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifecycle management"""
        logger = logging.getLogger(__name__)

        logger.info("Initializing ReAct manager...")
        from react.manager import react_manager
        await react_manager.initialize()
        logger.info("ReAct manager initialization completed")

        yield

        logger.info("Shutting down ReAct manager...")
        await react_manager.close()
        logger.info("ReAct manager has been shut down")

    app = FastAPI(
        title="Document Upload Service",
        description="Document upload/manage/analysis service API",
        version="0.1.0",
        debug=debug,
        openapi_url=server_config.base_url + '/openapi.json',
        lifespan=lifespan,
    )

    # Import all models to ensure they are registered with SQLAlchemy
    from structure.models.base import Base
    await db.create_all(Base)

    setup_routes(app, base_url=server_config.base_url)
    return app
