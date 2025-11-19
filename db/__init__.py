from __future__ import annotations

from typing import Optional, Dict, Any
import ssl as ssl_lib

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker


Base = declarative_base()


def _build_ssl_context(
    ssl_cert: Optional[str] = None,
    ssl_key: Optional[str] = None,
    ssl_ca: Optional[str] = None,
) -> Optional[ssl_lib.SSLContext]:
    """
    Build an SSL context if any client-side SSL files are provided.
    Returns None if no custom SSL context is needed.
    """
    if not any([ssl_cert, ssl_key, ssl_ca]):
        return None

    ctx = ssl_lib.create_default_context(cafile=ssl_ca)
    if ssl_cert and ssl_key:
        ctx.load_cert_chain(certfile=ssl_cert, keyfile=ssl_key)

    ctx.check_hostname = False
    return ctx


class DatabaseManager:
    """
    Async PostgreSQL session manager for FastAPI using SQLAlchemy 2.0+.
    """

    def __init__(self):
        self._engine = None
        self._session_factory = None

    def init(
        self,
        url: str,
        *,
        pool_size: int = 10,
        max_overflow: int = 20,
        echo: bool = False,
        echo_pool: bool = False,
        pool_pre_ping: bool = True,
        pool_recycle: int = 3600,
        connect_timeout: int = 30,
        command_timeout: Optional[int] = None,
        ssl_mode: Optional[str] = None,
        ssl_cert: Optional[str] = None,
        ssl_key: Optional[str] = None,
        ssl_ca: Optional[str] = None,
    ) -> None:
        """
        Initialize the async SQLAlchemy engine for PostgreSQL.

        :param url: Database URL (e.g., "postgresql+asyncpg://user:pass@host/db")
        :param pool_size: Number of connections to keep open inside the pool.
        :param max_overflow: Max number of connections to create above pool_size.
        :param echo: Enable SQL query logging.
        :param echo_pool: Enable connection pool logging.
        :param pool_pre_ping: Validate connections before use.
        :param pool_recycle: Recycle connections after this many seconds.
        :param connect_timeout: Connection timeout in seconds.
        :param command_timeout: Statement execution timeout in seconds.
        :param ssl_mode: SSL mode for asyncpg (e.g., "require", "verify-full").
        :param ssl_cert: Path to client SSL certificate file.
        :param ssl_key: Path to client SSL private key file.
        :param ssl_ca: Path to CA certificate file for server verification.
        """
        if self._engine is not None:
            raise RuntimeError("Database already initialized.")

        if not url:
            raise ValueError("Database URL must be provided.")

        # Build connect_args for asyncpg
        connect_args: Dict[str, Any] = {"timeout": connect_timeout}
        if command_timeout is not None:
            connect_args["command_timeout"] = command_timeout

        # Handle SSL
        if ssl_mode:
            ssl_setting = ssl_mode.lower()

            ssl_context = _build_ssl_context(ssl_cert, ssl_key, ssl_ca)
            if ssl_context:
                ssl_setting = ssl_context
            connect_args["ssl"] = ssl_setting

        self._engine = create_async_engine(
            url,
            echo=echo,
            echo_pool=echo_pool,
            pool_pre_ping=pool_pre_ping,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_recycle=pool_recycle,
            connect_args=connect_args,
        )

        self._session_factory = sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    def get_session(self) -> "_AsyncSessionContextManager":
        """
        Return an async context manager for database sessions.

        Usage:
            async with db.get_session() as session:
                await session.execute(...)
        """
        if self._session_factory is None:
            raise RuntimeError("Database not initialized. Call .init() first.")
        return _AsyncSessionContextManager(self._session_factory)

    async def create_all(self) -> None:
        """Create all tables defined on Base."""
        if self._engine is None:
            raise RuntimeError("Database not initialized.")
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def dispose(self) -> None:
        """Dispose of the engine and close all connections."""
        if self._engine:
            await self._engine.dispose()


class _AsyncSessionContextManager:
    """Async context manager that handles commit/rollback/close."""

    def __init__(self, session_factory):
        self._session_factory = session_factory
        self.session: Optional[AsyncSession] = None

    async def __aenter__(self) -> AsyncSession:
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


# Global instance (usage: db.init(...))
db = DatabaseManager()
