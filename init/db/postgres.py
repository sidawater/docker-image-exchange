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

    def init(
        self,
        url: str,
        pool_size: int = 0,
        max_overflow: int = 0,
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
        Initialize the async engine and session factory.
        Must be called before any database operations.

        Args:
            url: Database connection URL
            pool_size: Number of connections to maintain in the pool
            max_overflow: Max number of connections beyond pool_size
            echo: Log all SQL statements
            echo_pool: Log all pool checkouts/checkins
            pool_pre_ping: Test connections before using them
            pool_recycle: Recycle connections after N seconds
            connect_timeout: Connection timeout in seconds
            command_timeout: Command/query timeout in seconds (optional)
            ssl_mode: SSL mode for database connection
            ssl_cert: Path to SSL certificate file
            ssl_key: Path to SSL key file
            ssl_ca: Path to SSL CA file
        """
        if self._engine is not None:
            raise RuntimeError("Database already initialized.")

        # Build connect_args for PostgreSQL
        connect_args = {"timeout": connect_timeout}
        if command_timeout is not None:
            connect_args["command_timeout"] = command_timeout
        if ssl_mode is not None:
            connect_args["sslmode"] = ssl_mode
        if ssl_cert is not None:
            connect_args["sslcert"] = ssl_cert
        if ssl_key is not None:
            connect_args["sslkey"] = ssl_key
        if ssl_ca is not None:
            connect_args["sslca"] = ssl_ca

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


db = DatabaseManager()
