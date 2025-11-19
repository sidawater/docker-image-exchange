import asyncio
from typing import Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class _AsyncSessionContextManager:
    """
    An async context manager that yields a SQLAlchemy AsyncSession.
    Handles commit on success, rollback on exception, and close in all cases.
    """

    def __init__(self, session_factory):
        self._session_factory = session_factory
        self.session: Optional[AsyncSession] = None

    async def __aenter__(self) -> AsyncSession:
        if self._session_factory is None:
            raise RuntimeError("Session factory is not initialized.")
        self.session = self._session_factory()
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session is None:
            return
        try:
            if exc_type is not None:
                await self.session.rollback()
            else:
                await self.session.commit()
        finally:
            await self.session.close()


class DatabaseManager:
    """
    Manages async SQLAlchemy engine and provides session context managers
    for use in async applications (e.g., FastAPI).
    """

    def __init__(self):
        self._engine = None
        self._session_factory = None

    def init(self, database_url: str, echo: bool = False) -> None:
        """
        Initialize the async engine and session factory.
        Must be called before any database operations.
        """
        if self._engine is not None:
            raise RuntimeError("Database already initialized.")

        self._engine = create_async_engine(
            database_url,
            echo=echo,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
        self._session_factory = sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    def get_session(self) -> _AsyncSessionContextManager:
        """
        Returns an async context manager for database sessions.

        Usage:
            async with db.get_session() as session:
                await session.execute(...)
        """
        if self._session_factory is None:
            raise RuntimeError("Database not initialized. Call .init() first.")
        return _AsyncSessionContextManager(self._session_factory)

    async def create_all(self) -> None:
        """Create all tables."""
        if self._engine is None:
            raise RuntimeError("Database not initialized.")
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def dispose(self) -> None:
        """Dispose the engine on shutdown."""
        if self._engine:
            await self._engine.dispose()


# Global instance
db = DatabaseManager()
