"""
Async embedding client for Ollama embedding service.

Usage:
```python
    async with AsyncEmbeddingClient(
        base_url="http://localhost:11434",
        model_name="nomic-embed-text",
        embedding_dim=768,
    ) as client:
        embedding = await client.get_embedding("Hello world")
        embeddings = await client.get_embeddings(["text1", "text2"])
```
"""

import aiohttp
import asyncio
from typing import List, Optional
from http import HTTPStatus


class AsyncEmbeddingClient:
    """
    Asynchronous embedding client for Ollama embedding service.

    :param base_url: Ollama service base URL
    :type base_url: str
    :param model_name: Embedding model name
    :type model_name: str
    :param embedding_dim: Embedding vector dimension
    :type embedding_dim: int
    :param timeout: Request timeout in seconds
    :type timeout: int
    :param max_concurrent: Maximum concurrent requests
    :type max_concurrent: int
    """

    def __init__(
        self,
        base_url: str,
        model_name: str,
        embedding_dim: int,
        timeout: int = 300,
        max_concurrent: int = 10,
    ):
        """Initialize the async embedding client."""
        self.base_url = base_url.rstrip('/')
        self.model_name = model_name
        self.embedding_dim = embedding_dim
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_concurrent = max_concurrent
        self._session: Optional[aiohttp.ClientSession] = None
        self._semaphore = asyncio.Semaphore(max_concurrent)

    @property
    def session(self) -> aiohttp.ClientSession:
        """
        Get the aiohttp session.

        :return: Active aiohttp ClientSession
        :rtype: aiohttp.ClientSession
        :raises RuntimeError: If session not initialized
        """
        if self._session is None or self._session.closed:
            raise RuntimeError("Session not initialized. Use async context or call _ensure_session().")
        return self._session

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _ensure_session(self):
        """Ensure aiohttp session is created."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)

    async def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding vector for a single text.

        :param text: Input text
        :type text: str
        :return: Embedding vector
        :rtype: List[float]
        :raises RuntimeError: On network or API error
        """
        await self._ensure_session()
        payload = {"model": self.model_name, "prompt": text, "keep_alive": -1}

        async with self._semaphore:
            try:
                async with self.session.post(
                    f"{self.base_url}/api/embeddings", json=payload
                ) as response:
                    if response.status == HTTPStatus.OK:
                        result = await response.json()
                        return self._extract_embedding(result)
                    error_text = await response.text()
                    raise RuntimeError(f"Embedding failed: {response.status}, {error_text}")
            except aiohttp.ClientError as e:
                raise RuntimeError(f"Network error: {str(e)}")
            except asyncio.TimeoutError:
                raise RuntimeError(f"Request timeout after {self.timeout.total}s")

    def _extract_embedding(self, result: dict) -> List[float]:
        """
        Extract embedding from API response.

        :param result: API response dictionary
        :type result: dict
        :return: Embedding vector
        :rtype: List[float]
        :raises RuntimeError: If response format is unexpected
        """
        if "embedding" in result:
            return result["embedding"]
        if "embeddings" in result and len(result["embeddings"]) > 0:
            return result["embeddings"][0]["embedding"]
        raise RuntimeError(f"Unexpected response format: {result}")

    async def get_embeddings(
        self, texts: List[str], batch_size: Optional[int] = None
    ) -> List[List[float]]:
        """
        Get embedding vectors for multiple texts with batching.

        :param texts: List of input texts
        :type texts: List[str]
        :param batch_size: Batch size, defaults to max_concurrent
        :type batch_size: Optional[int]
        :return: List of embedding vectors
        :rtype: List[List[float]]
        """
        if not texts:
            return []
        if batch_size is None:
            batch_size = self.max_concurrent

        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            tasks = [self.get_embedding(text) for text in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for j, emb in enumerate(results):
                if isinstance(emb, Exception):
                    raise RuntimeError(f"Error at index {i+j}: {str(emb)}")
            all_embeddings.extend(results)
        return all_embeddings

    async def close(self):
        """Close the client session."""
        if self._session and not self._session.closed:
            await self._session.close()


class EmbeddingManager:
    """
    Manager class for embedding client initialization and lifecycle.
    """

    def __init__(self):
        self._client: Optional[AsyncEmbeddingClient] = None

    async def init(
        self,
        base_url: str,
        model_name: str,
        embedding_dim: int,
        timeout: int = 300,
        max_concurrent: int = 10,
    ) -> None:
        """
        Initialize the embedding client manager.

        :param base_url: Ollama service base URL
        :type base_url: str
        :param model_name: Embedding model name
        :type model_name: str
        :param embedding_dim: Embedding vector dimension
        :type embedding_dim: int
        :param timeout: Request timeout in seconds
        :type timeout: int
        :param max_concurrent: Maximum concurrent requests
        :type max_concurrent: int
        :raises RuntimeError: If manager already initialized
        """
        if self._client is not None:
            raise RuntimeError("EmbeddingManager already initialized.")

        self._client = AsyncEmbeddingClient(
            base_url=base_url,
            model_name=model_name,
            embedding_dim=embedding_dim,
            timeout=timeout,
            max_concurrent=max_concurrent,
        )
        await self._client._ensure_session()

    @property
    def client(self) -> AsyncEmbeddingClient:
        """
        Get the embedding client instance.

        :return: AsyncEmbeddingClient instance
        :rtype: AsyncEmbeddingClient
        :raises RuntimeError: If manager not initialized
        """
        if self._client is None:
            raise RuntimeError("EmbeddingManager not initialized. Call .init() first.")
        return self._client

    async def close(self) -> None:
        """Close the embedding client manager."""
        if self._client:
            await self._client.close()
        self._client = None


embedding_manager: EmbeddingManager = EmbeddingManager()


def get_embedding_manager() -> EmbeddingManager:
    """
    Get the global EmbeddingManager instance.

    :return: Global EmbeddingManager instance
    :rtype: EmbeddingManager
    """
    return embedding_manager
