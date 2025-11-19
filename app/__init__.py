from fastapi import FastAPI
from app.subapps.items import router as items_router
from db import DatabaseManager


def create_app() -> FastAPI:
    app = FastAPI(
        title="My Simple FastAPI App",
        description="A minimal FastAPI structure with subapps and ORM models",
        version="0.1.0"
    )

    from config import init_settings, DatabaseConfig
    settings = init_settings()
    db_config = DatabaseConfig.load_from_settings(settings=settings)
    DatabaseManager.init(**db_config.as_dict())

    app.include_router(items_router, prefix="/api/v1")
    return app
