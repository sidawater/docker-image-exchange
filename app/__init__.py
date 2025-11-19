from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.file.api import DocFile
from init.db import db, redis_manager
from init.db.redis.stream import init_stream_queue_manager
from init.config import init_settings, DatabaseConfig, RedisConfig, StorageConfig


def setup_routes(app: FastAPI) -> None:
    from app.subapps.doc.route import router as doc_router
    app.include_router(doc_router, prefix="/doc")


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     pass


async def create_app(debug: bool = False) -> FastAPI:
    app = FastAPI(
        title="Document Upload Service",
        description="Document upload/management/analysis service API",
        version="0.1.0",
        debug=debug,
        # lifespan=lifespan,
    )

    # Initialize database and cache managers
    settings = init_settings()
    db_config = DatabaseConfig.load_from_settings(settings=settings)
    db.init(**db_config.as_dict())
    redis_config = RedisConfig.load_from_settings(settings=settings)
    await redis_manager.init(**redis_config.as_dict())
    await init_stream_queue_manager(redis_manager)

    # Initialize core storage (DocFile) with configuration
    storage_config = StorageConfig.load_from_settings(settings=settings)
    DocFile.init(**storage_config.as_dict())

    setup_routes(app)
    return app
