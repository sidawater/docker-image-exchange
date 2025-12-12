"""
Qdrant client with async support using qdrant-client.

Usage:
```python
    qdrant_client = AsyncQdrantClient(
        host="localhost",
        port=6333,
        api_key="your-api-key",
        timeout=120
    )

    # Test connection
    health = await qdrant_client.health()
    print("Qdrant health:", health)

    # Create collection
    await qdrant_client.create_collection(
        collection_name="test-collection",
        vectors_config=VectorParams(size=768, distance=Distance.COSINE)
    )
    print("Created collection: test-collection")

    # Insert points
    points = [
        PointStruct(id=1, vector=[0.1] * 768, payload={"text": "Document 1"}),
        PointStruct(id=2, vector=[0.2] * 768, payload={"text": "Document 2"}),
    ]
    await qdrant_client.upsert(
        collection_name="test-collection",
        points=points
    )
    print("Inserted points")

    # Search similar vectors
    search_results = await qdrant_client.search(
        collection_name="test-collection",
        query_vector=[0.15] * 768,
        limit=5
    )
    print("Search results:", search_results)

    # Get points
    points = await qdrant_client.retrieve(
        collection_name="test-collection",
        ids=[1, 2]
    )
    print("Retrieved points:", points)

    # Update points
    await qdrant_client.set_payload(
        collection_name="test-collection",
        payload={"category": "updated"},
        points=[1]
    )
    print("Updated point payload")

    # Delete points
    await qdrant_client.delete(
        collection_name="test-collection",
        points_selector=[1, 2]
    )
    print("Deleted points")

    # List collections
    collections = await qdrant_client.get_collections()
    print("Available collections:", collections.collections)

    # Get collection info
    collection_info = await qdrant_client.get_collection(
        collection_name="test-collection"
    )
    print("Collection info:", collection_info)

    # Delete collection
    await qdrant_client.delete_collection("test-collection")
    print("Deleted collection")
```
"""

from typing import Optional, List, Dict, Any, Union, Tuple
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import (
    VectorParams,
    VectorParamsDiff,
    PointStruct,
    Filter,
    SearchRequest,
    CollectionInfo,
    CollectionsResponse,
    Record,
    NearestQuery,
    ScoredPoint,
)


class AsyncQdrantClientWrapper:
    """
    Asynchronous Qdrant client wrapper providing async operations.

    This client wraps qdrant_client.AsyncQdrantClient to provide a more
    Pythonic async interface with proper resource management.

    :param host: Qdrant server host
    :type host: str
    :param port: Qdrant server port
    :type port: int
    :param api_key: API key for authentication (optional)
    :type api_key: str
    :param timeout: Request timeout in seconds
    :type timeout: int
    :param prefer_grpc: Prefer GRPC transport over HTTP
    :type prefer_grpc: bool
    """

    def __init__(
        self,
        host: str,
        port: int,
        grpc_port: int,
        api_key: Optional[str] = None,
        timeout: int = 120,
        prefer_grpc: bool = False,
    ):
        """Initialize the async Qdrant client."""
        self.host = host
        self.port = port
        self.grpc_port = grpc_port
        self.api_key = api_key
        self.timeout = timeout
        self.prefer_grpc = prefer_grpc

        self._client: Optional[AsyncQdrantClient] = None

    @property
    def client(self) -> AsyncQdrantClient:
        """
        Get the Qdrant client instance.

        :returns: AsyncQdrantClient instance
        :raises RuntimeError: If client not initialized
        """
        if self._client is None:
            raise RuntimeError("QdrantClient not initialized. Call .init() first.")
        return self._client

    async def init(self) -> None:
        """
        Initialize the Qdrant client connection.
        """
        # Create Qdrant client with proper configuration
        client_kwargs = {
            'host': self.host,
            'port': self.port,
            'grpc_port': self.grpc_port,
            'timeout': self.timeout,
        }

        if self.api_key:
            client_kwargs['api_key'] = self.api_key

        # Only set prefer_grpc if it's True
        if self.prefer_grpc:
            client_kwargs['prefer_grpc'] = True

        self._client = AsyncQdrantClient(**client_kwargs)

    async def close(self) -> None:
        """
        Close the Qdrant client connection.
        """
        if self._client is not None:
            await self._client.close()
            self._client = None

    # Collection operations
    async def get_collections(self) -> CollectionsResponse:
        """
        Get list of all collections.

        :return: Collections response
        :rtype: CollectionsResponse
        """
        return await self.client.get_collections()

    async def create_collection(
        self,
        collection_name: str,
        vectors_config: Union[VectorParams, Dict[str, VectorParams]],
        **kwargs
    ) -> bool:
        """
        Create a new collection.

        :param collection_name: Name of the collection
        :type collection_name: str
        :param vectors_config: Vector parameters
        :type vectors_config: Union[VectorParams, Dict[str, VectorParams]]
        :return: True if successful
        :rtype: bool
        """
        try:
            await self.client.create_collection(
                collection_name=collection_name,
                vectors_config=vectors_config,
                **kwargs
            )
            return True
        except Exception as e:
            print(f"Failed to create collection: {e}")
            return False

    async def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection.

        :param collection_name: Name of the collection to delete
        :type collection_name: str
        :return: True if successful
        :rtype: bool
        """
        try:
            await self.client.delete_collection(collection_name=collection_name)
            return True
        except Exception as e:
            print(f"Failed to delete collection: {e}")
            return False

    async def collection_exists(self, collection_name: str) -> bool:
        """
        Check if a collection exists.

        :param collection_name: Name of the collection
        :type collection_name: str
        :return: True if collection exists
        :rtype: bool
        """
        try:
            collections = await self.get_collections()
            return any(c.name == collection_name for c in collections.collections)
        except Exception as e:
            print(f"Failed to check collection existence: {e}")
            return False

    async def get_collection(self, collection_name: str) -> CollectionInfo:
        """
        Get collection information.

        :param collection_name: Name of the collection
        :type collection_name: str
        :return: Collection information
        :rtype: CollectionInfo
        """
        return await self.client.get_collection(collection_name=collection_name)

    async def update_collection(
        self,
        collection_name: str,
        vectors_config_diff: Optional[VectorParamsDiff] = None,
    ) -> bool:
        """
        Update collection parameters.

        :param collection_name: Name of the collection
        :type collection_name: str
        :param vectors_config_diff: Vector configuration changes
        :type vectors_config_diff: Optional[VectorParamsDiff]
        :return: True if successful
        :rtype: bool
        """
        try:
            await self.client.update_collection(
                collection_name=collection_name,
                vectors_config_diff=vectors_config_diff
            )
            return True
        except Exception as e:
            print(f"Failed to update collection: {e}")
            return False

    # Point operations
    async def upsert(
        self,
        collection_name: str,
        points: Union[List[PointStruct], List[Dict]],
        **kwargs
    ) -> bool:
        """
        Insert or update points in a collection.

        :param collection_name: Name of the collection
        :type collection_name: str
        :param points: Points to insert/update
        :type points: Union[List[PointStruct], List[Dict]]
        :return: True if successful
        :rtype: bool
        """
        try:
            await self.client.upsert(
                collection_name=collection_name,
                points=points,  # type: ignore
                **kwargs
            )
            return True
        except Exception as e:
            print(f"Failed to upsert points: {e}")
            return False

    async def search(
        self,
        collection_name: str,
        query_vector: Union[List[float], List[List[float]]],
        limit: int = 10,
        **kwargs
    ) -> List[ScoredPoint]:
        """
        Search for similar vectors.

        :param collection_name: Name of the collection
        :type collection_name: str
        :param query_vector: Query vector(s)
        :type query_vector: Union[List[float], List[List[float]]]
        :param limit: Maximum number of results
        :type limit: int
        :return: List of matching records
        :rtype: List[ScoredPoint]
        """
        if isinstance(query_vector[0], list):
            query = NearestQuery(nearest=query_vector[0])
        else:
            query = NearestQuery(nearest=query_vector)

        query = await self.client.query_points(
            collection_name=collection_name,
            query=query,
            limit=limit,
            with_payload=True,
            with_vectors=False,
            **kwargs
        )

        return query.points

    async def retrieve(
        self,
        collection_name: str,
        ids: List[int],
        **kwargs
    ) -> List[Record]:
        """
        Retrieve points by ID.

        :param collection_name: Name of the collection
        :type collection_name: str
        :param ids: Point IDs to retrieve
        :type ids: List[int]
        :return: List of records
        :rtype: List[Record]
        """
        return await self.client.retrieve(
            collection_name=collection_name,
            ids=ids,  # type: ignore
            **kwargs
        )

    async def delete(
        self,
        collection_name: str,
        points_selector: Union[List[int], Filter],
        **kwargs
    ) -> bool:
        """
        Delete points from a collection.

        :param collection_name: Name of the collection
        :type collection_name: str
        :param points_selector: Points or filter to delete
        :type points_selector: Union[List[int], Filter]
        :return: True if successful
        :rtype: bool
        """
        try:
            await self.client.delete(
                collection_name=collection_name,
                points_selector=points_selector,  # type: ignore
                **kwargs
            )
            return True
        except Exception as e:
            print(f"Failed to delete points: {e}")
            return False

    async def set_payload(
        self,
        collection_name: str,
        payload: Dict[str, Any],
        points: Optional[List[int]] = None,
        **kwargs
    ) -> bool:
        """
        Set payload for points.

        :param collection_name: Name of the collection
        :type collection_name: str
        :param payload: Payload to set
        :type payload: Dict[str, Any]
        :param points: Points to update (None for all)
        :type points: Optional[List[int]]
        :return: True if successful
        :rtype: bool
        """
        try:
            await self.client.set_payload(
                collection_name=collection_name,
                payload=payload,
                points=points,  # type: ignore
                **kwargs
            )
            return True
        except Exception as e:
            print(f"Failed to set payload: {e}")
            return False

    async def delete_payload(
        self,
        collection_name: str,
        keys: List[str],
        points: Optional[List[int]] = None,
        **kwargs
    ) -> bool:
        """
        Delete payload keys from points.

        :param collection_name: Name of the collection
        :type collection_name: str
        :param keys: Payload keys to delete
        :type keys: List[str]
        :param points: Points to update (None for all)
        :type points: Optional[List[int]]
        :return: True if successful
        :rtype: bool
        """
        try:
            await self.client.delete_payload(
                collection_name=collection_name,
                keys=keys,
                points=points,  # type: ignore
                **kwargs
            )
            return True
        except Exception as e:
            print(f"Failed to delete payload: {e}")
            return False

    async def scroll(
        self,
        collection_name: str,
        limit: int = 10,
        **kwargs
    ) -> Tuple[List[Record], Any]:
        """
        Scroll through points in a collection.

        :param collection_name: Name of the collection
        :type collection_name: str
        :param limit: Maximum number of results
        :type limit: int
        :return: Tuple of (records, next_page_offset)
        :rtype: Tuple[List[Record], Any]
        """
        return await self.client.scroll(
            collection_name=collection_name,
            limit=limit,
            **kwargs
        )

    async def count(
        self,
        collection_name: str,
        **kwargs
    ) -> Any:
        """
        Count points in a collection.

        :param collection_name: Name of the collection
        :type collection_name: str
        :return: Number of points
        :rtype: Any
        """
        result = await self.client.count(
            collection_name=collection_name,
            **kwargs
        )
        return result.count

    # Aliases for common operations
    async def insert(self, collection_name: str, points: Union[List[PointStruct], List[Dict]], **kwargs) -> bool:
        """
        Alias for upsert (insert points).

        :param collection_name: Name of the collection
        :type collection_name: str
        :param points: Points to insert
        :type points: Union[List[PointStruct], List[Dict]]
        :return: True if successful
        :rtype: bool
        """
        return await self.upsert(collection_name, points, **kwargs)

    async def search_batch(
        self,
        collection_name: str,
        requests: List[SearchRequest],
        **kwargs
    ) -> Any:
        """
        Perform batch searches.

        :param collection_name: Name of the collection
        :type collection_name: str
        :param requests: List of search requests
        :type requests: List[SearchRequest]
        :return: List of search results
        :rtype: Any
        """
        return await self.client.query_batch_points(
            collection_name=collection_name,
            queries=[{'search': req} for req in requests],
            **kwargs
        )

    async def health(self) -> Dict[str, Any]:
        """
        Get Qdrant server health status.

        :return: Health information
        :rtype: Dict[str, Any]
        """
        try:
            collections = await self.get_collections()
            return {
                "status": "healthy",
                "collections_count": len(collections.collections)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


class QdrantManager:
    """
    Manager class for Qdrant client initialization and lifecycle management.
    """

    def __init__(self):
        self._client: Optional[AsyncQdrantClientWrapper] = None

    async def init(
        self,
        host: str,
        port: int,
        grpc_port: int,
        api_key: Optional[str] = None,
        timeout: int = 60,
        prefer_grpc: bool = True
    ) -> None:
        """
        Initialize the Qdrant client manager.

        :param host: Qdrant server host
        :type host: str
        :param port: Qdrant server port
        :type port: int
        :param api_key: API key for authentication
        :type api_key: Optional[str]
        :param timeout: Request timeout in seconds
        :type timeout: int
        :param prefer_grpc: Prefer GRPC transport over HTTP
        :type prefer_grpc: bool
        :returns: None
        :raises RuntimeError: If manager already initialized
        """
        if self._client is not None:
            raise RuntimeError("QdrantManager already initialized.")

        self._client = AsyncQdrantClientWrapper(
            host=host,
            port=port,
            grpc_port=grpc_port,
            api_key=api_key,
            timeout=timeout,
            prefer_grpc=prefer_grpc,
        )

        await self._client.init()

        # Test connection
        try:
            health = await self._client.health()
            if health["status"] != "healthy":
                self._client = None
                raise RuntimeError(f"Failed to connect to Qdrant: {health}")
        except Exception as e:
            self._client = None
            raise RuntimeError(f"Failed to connect to Qdrant: {e}")

    @property
    def client(self) -> AsyncQdrantClientWrapper:
        """
        Get the Qdrant client instance.

        :returns: AsyncQdrantClientWrapper instance
        :raises RuntimeError: If manager not initialized
        """
        if self._client is None:
            raise RuntimeError("QdrantManager not initialized. Call .init() first.")
        return self._client

    async def close(self) -> None:
        """Close the Qdrant client manager."""
        if self._client is not None:
            await self._client.close()
            self._client = None


qdrant_manager: QdrantManager = QdrantManager()


def get_qdrant_manager() -> QdrantManager:
    """
    Get the global QdrantManager instance.

    :returns: Global QdrantManager instance
    """
    return qdrant_manager


if __name__ == '__main__':
    import asyncio

    async def test():
        res = await qdrant_manager.init(
            host="10.194.203.138",
            port=16333,
            grpc_port=16334,
        )
        print(res)
    
    asyncio.run(test())
