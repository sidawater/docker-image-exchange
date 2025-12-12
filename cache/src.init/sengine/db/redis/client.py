import inspect
from typing import Optional
from redis.asyncio import Redis, ConnectionPool
from redis.exceptions import ConnectionError as RedisConnectionError


class RedisManager:
    """
    Asynchronous Redis connection manager.
    """

    def __init__(self):
        self._client: Optional[Redis] = None
        self._pool: Optional[ConnectionPool] = None

    async def init(
        self,
        url: str,
        max_connections: int = 50,
        encoding: str = "utf-8",
        decode_responses: bool = True,
        socket_connect_timeout: int = 5,
        socket_timeout: int = 5,
        health_check_interval: int = 30,
        retry_on_timeout: bool = True,
    ) -> None:
        """
        Initialize asynchronous Redis connection.

        :param url: Redis connection URL (e.g., 'redis://localhost:6379/0')
        :param max_connections: Maximum number of connections in pool (default: 50)
        :param encoding: String encoding format (default: "utf-8")
        :param decode_responses: Automatically decode responses to strings (default: True)
        :param socket_connect_timeout: Socket connection timeout in seconds (default: 5)
        :param socket_timeout: Socket timeout in seconds (default: 5)
        :param health_check_interval: Health check interval in seconds (default: 30)
        :param retry_on_timeout: Retry on socket timeout (default: True)
        :returns: None
        :raises RuntimeError: If manager already initialized
        :raises RuntimeError: If connection test fails
        """
        if self._client is not None:
            raise RuntimeError("RedisManager already initialized.")

        # Build connection kwargs
        connection_kwargs = {
            'max_connections': max_connections,
            'encoding': encoding,
            'decode_responses': decode_responses,
            'socket_connect_timeout': socket_connect_timeout,
            'socket_timeout': socket_timeout,
            'health_check_interval': health_check_interval,
            'retry_on_timeout': retry_on_timeout,
        }

        # Create connection pool and client
        self._pool = ConnectionPool.from_url(url, **connection_kwargs)
        self._client = Redis(connection_pool=self._pool)

        # Test connection using ping() without parameters (compatible with redis-py 5.x and 7.x)
        try:
            ping_result = self._client.ping()
            if inspect.isawaitable(ping_result):
                # Async mode (redis-py 5.x and 7.x in async context)
                await ping_result
            # In sync mode, result would already be a boolean
        except RedisConnectionError as e:
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
