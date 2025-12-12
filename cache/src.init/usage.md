# SEngine Usage Guide

## Overview

SEngine is an enterprise-grade backend infrastructure library for AI dialogue systems. It provides comprehensive support for conversation management, AI reasoning services, document processing, and multi-modal interactions.

## Architecture

The library is organized into four main modules:

```
sengine/
- config/          # Configuration management
- db/              # Database abstraction layer
- msg/             # Message service client
- utils/           # Utility functions
```

## Core Features

- **Configuration Management**: Multi-source config loading (env vars, dict, object, TOML)
- **Database Support**: PostgreSQL (async), Redis (caching & queues), MinIO/S3 (object storage)
- **Message Service**: HTTP client for conversation APIs
- **AI Integration**: vLLM, Embedding models, ReAct framework
- **Vector Storage**: Qdrant vector database integration
- **Async Architecture**: Full async/await support throughout

## Quick Start

### 1. Configuration

The library uses a centralized configuration system with multiple loaders:

```python
from sengine.config.base import Settings
from sengine.config.container.loader import load_from_toml

# Load from TOML file
settings = load_from_toml("config.toml")

# Load from environment variables
settings = Settings()

# Load from dictionary
config_dict = {...}
settings = Settings(**config_dict)
```

### 2. Database Connections

#### PostgreSQL

```python
from sengine.db.postgres import DatabaseManager
from sengine.config.database import DatabaseConfig

db_config = DatabaseConfig(
    url="postgresql+asyncpg://user:pass@localhost/db",
    pool_size=10
)

db_manager = DatabaseManager(db_config)

# Use async session
async with db_manager.get_session() as session:
    result = await session.execute(select(User))
```

#### Redis

```python
from sengine.db.redis.client import RedisManager
from sengine.config.redis import RedisConfig

redis_config = RedisConfig(
    url="redis://localhost:6379/0"
)

redis_manager = RedisManager(redis_config)
await redis_manager.connect()
```

#### Redis Stream (Message Queue)

```python
from sengine.db.redis.stream import StreamQueueManager

queue = StreamQueueManager(
    redis_manager=redis_manager,
    stream_name="my_stream",
    consumer_group="my_group",
    consumer_name="consumer1"
)

# Produce message
await queue.add_message({"task": "process_document", "data": "..."})

# Consume messages
async for message in queue.consume():
    print(f"Received: {message}")
    await queue.ack(message['id'])
```

#### MinIO/S3 Object Storage

```python
from sengine.db.s3.kminio import MinioManager
from sengine.config.storage import StorageConfig

storage_config = StorageConfig(
    backend="minio",
    endpoint="localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin"
)

storage_manager = MinioManager(storage_config)

# Upload file
await storage_manager.upload_file(
    bucket="my-bucket",
    object_name="document.pdf",
    file_path="/path/to/file.pdf"
)

# Generate presigned URL
url = await storage_manager.get_presigned_url(
    bucket="my-bucket",
    object_name="document.pdf",
    expires=3600
)
```

### 3. Message Service Client

```python
from sengine.msg.client import MessageClient
from sengine.msg.session import SessionClient
from sengine.msg.qa import QaClient
from sengine.msg.attachment import AttachmentClient
from sengine.msg.react import ReActClient

# Initialize client
client = MessageClient(base_url="http://localhost:8000")

# Session management
session_client = client.session

# Create session
session = await session_client.create(
    user_id="user123",
    title="My Conversation"
)

# Get session
session = await session_client.get(session_id="session123")

# List sessions
sessions = await session_client.list(user_id="user123")

# QA Records
qa_client = client.qa

# Create QA record
qa = await qa_client.create(
    session_id="session123",
    question="What is AI?",
    answer="AI is Artificial Intelligence..."
)

# Search QA records
results = await qa_client.search(
    query="machine learning",
    limit=10
)

# Attachments
attachment_client = client.attachment

# Upload attachment
attachment = await attachment_client.upload(
    file_path="/path/to/document.pdf",
    session_id="session123"
)

# Get download URL
download_url = await attachment_client.get_download_url(
    attachment_id="att123"
)

# ReAct Instances
react_client = client.react

# Create ReAct instance
react = await react_client.create(
    name="my_react",
    config={
        "llm": {...},
        "tools": [...]
    }
)

# Test connection
result = await react_client.test(instance_id="react123")
```

### 4. Using ReAct Framework

```python
from sengine.msg.react import ReActClient

react_client = client.react

# Create ReAct instance with LLM and tools
react_instance = await react_client.create(
    name="data_analyzer",
    config={
        "llm": {
            "model": "gpt-4",
            "temperature": 0.7
        },
        "mcp_servers": [
            {
                "name": "filesystem",
                "command": "python",
                "args": ["mcp_server.py"]
            }
        ],
        "rag": {
            "enabled": True,
            "vector_db": "qdrant",
            "collection": "documents"
        }
    }
)

# Clone instance
cloned = await react_client.clone(
    instance_id="react123",
    name="cloned_react"
)

# Update configuration
await react_client.update_config(
    instance_id="react123",
    config={...}
)
```

### 5. Configuration Options

#### Server Configuration

```python
from sengine.config.server import ServerConfig

server_config = ServerConfig(
    host="0.0.0.0",
    port=8000,
    reload=True,
    base_url="http://localhost:8000"
)
```

#### LLM Configuration

```python
from sengine.config.llm import LLMConfig, EmbeddingConfig

llm_config = LLMConfig(
    base_url="http://localhost:8000/v1",
    model="meta-llama/Llama-2-70b-chat-hf",
    api_key="your-api-key",
    max_tokens=4096,
    temperature=0.7
)

embedding_config = EmbeddingConfig(
    base_url="http://localhost:8001/v1",
    model="BAAI/bge-large-en-v1.5"
)
```

#### Vector Database Configuration

```python
from sengine.config.vector import QdrantConfig

qdrant_config = QdrantConfig(
    host="localhost",
    port=6333,
    grpc_port=6334,
    api_key="your-api-key",
    collection_name="documents"
)
```

## API Endpoints

### Session Management
- `POST /messages/sessions` - Create session
- `GET /messages/sessions/{session_id}` - Get session
- `GET /messages/sessions` - List sessions
- `PUT /messages/sessions/{session_id}` - Update session
- `DELETE /messages/sessions/{session_id}` - Delete session

### QA Records
- `POST /messages/qa` - Create QA record
- `GET /messages/qa/{qa_id}` - Get QA record
- `PUT /messages/qa/{qa_id}` - Update QA record
- `GET /messages/qa/search` - Search QA records
- `GET /messages/qa/session/{session_id}` - Get session QA records

### Attachments
- `POST /knowledge/message-service/attachments/upload` - Upload attachment
- `GET /knowledge/message-service/attachments/{attachment_id}` - Get attachment
- `GET /knowledge/message-service/attachments/{attachment_id}/url` - Get download URL
- `DELETE /knowledge/message-service/attachments/{attachment_id}` - Delete attachment

### ReAct Instances
- `POST /knowledge/message-service/react` - Create ReAct instance
- `GET /knowledge/message-service/react/{instance_id}` - Get instance
- `GET /knowledge/message-service/react` - List instances
- `PUT /knowledge/message-service/react/{instance_id}` - Update instance
- `DELETE /knowledge/message-service/react/{instance_id}` - Delete instance
- `PUT /knowledge/message-service/react/{instance_id}/config` - Update config
- `PUT /knowledge/message-service/react/{instance_id}/status` - Update status
- `POST /knowledge/message-service/react/{instance_id}/test` - Test connection
- `POST /knowledge/message-service/react/{instance_id}/clone` - Clone instance

## Best Practices

### 1. Async/Await Usage
Always use async/await patterns with the library:

```python
async def main():
    # Use async context managers
    async with db_manager.get_session() as session:
        await session.execute(...)

    # Properly close connections
    await redis_manager.close()
    await storage_manager.close()
```

### 2. Connection Pool Management
The library provides built-in connection pooling. No need to manually manage connections for each request:

```python
# Database pool is automatically managed
db_manager = DatabaseManager(db_config)

# Redis connection pool
redis_manager = RedisManager(redis_config)
await redis_manager.connect()
```

### 3. Error Handling
The library provides specific exceptions:

```python
from sengine.msg.exceptions import (
    MessageServiceError,
    ValidationError,
    NotFoundError,
    AuthenticationError,
    ServerError
)

try:
    session = await session_client.get("invalid_id")
except NotFoundError:
    print("Session not found")
except ValidationError as e:
    print(f"Invalid request: {e}")
except MessageServiceError as e:
    print(f"Service error: {e}")
```

### 4. Configuration Loading
Load configuration from the most appropriate source:

```python
# Development: Use environment variables
settings = Settings()

# Production: Use TOML file
settings = load_from_toml("/etc/app/config.toml")

# Testing: Use dictionary
settings = Settings(**test_config)
```

### 5. Message Queue Patterns

Use Redis Stream for reliable message processing:

```python
# Producer
await queue.add_message(
    {"task": "process", "id": "123"},
    maxlen=10000  # Limit stream length
)

# Consumer with auto-retry
async for message in queue.consume():
    try:
        await process_message(message)
        await queue.ack(message['id'])
    except Exception as e:
        await queue.nack(message['id'])  # Retry
        raise
```

## Advanced Features

### Custom Configuration Loaders

Create custom configuration loaders by implementing the `Loadable` interface:

```python
from sengine.config.container.objects import Loadable

class CustomConfig(Loadable):
    def load_from_object(self, obj):
        # Custom loading logic
        pass
```

### Batch Operations

For high-throughput scenarios, use batch operations:

```python
# Batch upload to MinIO
await storage_manager.batch_upload(
    bucket="my-bucket",
    files=[
        ("file1.pdf", "/path/to/file1.pdf"),
        ("file2.pdf", "/path/to/file2.pdf")
    ]
)

# Batch delete from Redis stream
await queue.batch_delete(message_ids=["id1", "id2", "id3"])
```

### Health Checks

Monitor service health:

```python
# Check database connection
await db_manager.health_check()

# Check Redis connection
await redis_manager.ping()

# Check MinIO connection
await storage_manager.bucket_exists("my-bucket")
```

## Monitoring and Metrics

The library includes built-in metrics collection for Redis Stream:

```python
queue = StreamQueueManager(...)

# Get queue statistics
stats = await queue.get_stats()
print(f"Stream length: {stats['stream_length']}")
print(f"Consumer lag: {stats['consumer_lag']}")
```

## Security Considerations

1. **API Keys**: Store API keys in environment variables or secure vaults
2. **TLS/SSL**: Enable SSL for all database connections
3. **Access Control**: Implement proper access control for ReAct instances
4. **Data Validation**: All inputs are validated using Pydantic models
5. **Presigned URLs**: Use presigned URLs for secure file access

## Troubleshooting

### Common Issues

1. **Connection Timeouts**
   - Check network connectivity
   - Verify connection pool settings
   - Increase timeout values

2. **Memory Issues**
   - Adjust connection pool sizes
   - Monitor stream lengths
   - Use batch operations for large datasets

3. **Configuration Errors**
   - Verify all required fields are present
   - Check environment variable names
   - Validate TOML file syntax

### Debug Mode

Enable debug mode in configuration:

```python
from sengine.config.base import Settings

settings = Settings(
    app_name="MyApp",
    debug=True
)
```

## Performance Optimization

1. **Connection Pooling**: Use appropriate pool sizes
2. **Async Operations**: Ensure all I/O operations are async
3. **Batch Processing**: Use batch operations for bulk data
4. **Caching**: Leverage Redis for caching frequently accessed data
5. **Indexing**: Use database indexes for search operations

## License

This library is part of the SEngine project.
