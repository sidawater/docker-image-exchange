from typing import Optional
from redis.asyncio import Redis, ConnectionPool


class RedisManager:
    """
    Asynchronous Redis connection manager.
    """

    def __init__(self):
        self._client: Optional[Redis] = None
        self._pool: Optional[ConnectionPool] = None

    async def init(self, url: str, **kwargs) -> None:
        """
        Initialize asynchronous Redis connection.
        
        :param redis_url: Redis connection URL (e.g., 'redis://localhost:6379/0')
        :param kwargs: Additional Redis connection parameters
        :returns: None
        """
        if self._client is not None:
            raise RuntimeError("RedisManager already initialized.")

        connection_kwargs = {
            'decode_responses': True,
            'socket_connect_timeout': 5,
            'retry_on_timeout': True,
            **kwargs
        }

        self._pool = ConnectionPool.from_url(url, **connection_kwargs)
        self._client = Redis(connection_pool=self._pool)

        try:
            await self._client.ping()
        except ConnectionError as e:
            await self.close()
            raise RuntimeError(f"Failed to connect to Redis: {e}")

    @property
    def client(self) -> Redis:
        """
        Get asynchronous Redis client instance.
        
        :returns: Asynchronous Redis client instance
        :raises RuntimeError: If manager not initialized
        """
        if self._client is None:
            raise RuntimeError("RedisManager not initialized. Call .init() first.")
        return self._client

    async def close(self) -> None:
        """Close Redis connection and connection pool."""
        if self._client is not None:
            await self._client.close()
            self._client = None
        
        if self._pool is not None:
            await self._pool.disconnect()
            self._pool = None


redis_manager: RedisManager = RedisManager()


def get_redis_manager() -> RedisManager:
    """
    Get the global RedisManager instance.
    :returns: Global RedisManager instance
    """
    return redis_manager
