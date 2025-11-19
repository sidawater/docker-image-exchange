import asyncio
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
import logging
from redis.asyncio import Redis
from redis.exceptions import ResponseError
from .client import RedisManager

logger = logging.getLogger(__name__)


class StreamQueueError(Exception):
    """Base exception class for Stream queue operations."""
    pass


class ConsumerError(StreamQueueError):
    """Exception raised for consumer-related errors."""
    pass


class MessageStatus(Enum):
    """Enumeration of message processing statuses."""
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


@dataclass
class StreamMessage:
    """Data class representing a Stream message."""
    message_id: str
    fields: Dict[str, Any]
    stream_name: str
    consumer_group: Optional[str] = None
    consumer_name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'message_id': self.message_id,
            'fields': self.fields,
            'stream_name': self.stream_name,
            'consumer_group': self.consumer_group,
            'consumer_name': self.consumer_name
        }


@dataclass
class ConsumerConfig:
    """Configuration for Stream consumers."""
    batch_size: int = 10
    block_time_ms: int = 5000
    auto_ack: bool = False
    max_retries: int = 3
    dead_letter_stream: Optional[str] = None
    max_len: Optional[int] = 10000  # Maximum stream length
    health_check_interval: int = 30  # Health check interval in seconds


class StreamConsumer:
    """
    Base class for Stream consumers.
    
    Subclasses must implement the process_message method.
    """
    
    def __init__(self, name: str, stream_name: str, config: ConsumerConfig = None):
        self.name = name
        self.stream_name = stream_name
        self.config = config or ConsumerConfig()
        self._is_running = False
        self._processing_tasks: List[asyncio.Task] = []
        self._processed_count = 0
        self._failed_count = 0
    
    async def process_message(self, message: StreamMessage) -> bool:
        """
        Abstract method to process a message. Must be implemented by subclasses.
        
        :param message: Stream message to process
        :return: True if processing succeeded, False otherwise
        """
        raise NotImplementedError("Subclasses must implement process_message method")
    
    async def on_message(self, message: StreamMessage) -> bool:
        """
        Message processing entry point with error handling and retry logic.
        
        :param message: Stream message to process
        :return: True if processing succeeded, False otherwise
        """
        for attempt in range(self.config.max_retries + 1):
            try:
                success = await self.process_message(message)
                if success:
                    self._processed_count += 1
                    logger.info(f"Consumer {self.name} successfully processed message {message.message_id}")
                    return True
                else:
                    logger.warning(f"Consumer {self.name} returned failure for message {message.message_id}")
                    
            except Exception as e:
                logger.error(f"Consumer {self.name} error processing message {message.message_id} (attempt {attempt + 1}): {e}")
                
                if attempt == self.config.max_retries:
                    self._failed_count += 1
                    await self._handle_failed_message(message, str(e))
                    return False
            
            if attempt < self.config.max_retries:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return False
    
    async def _handle_failed_message(self, message: StreamMessage, error: str):
        """
        Handle messages that failed after all retry attempts.
        
        :param message: Failed message
        :param error: Error description
        """
        logger.error(f"Message {message.message_id} failed after {self.config.max_retries} retries: {error}")
        
        # Send to dead letter stream if configured
        if self.config.dead_letter_stream:
            try:
                dead_letter_data = {
                    'original_message': message.fields,
                    'original_stream': message.stream_name,
                    'original_message_id': message.message_id,
                    'failure_reason': error,
                    'failed_at': asyncio.get_event_loop().time(),
                    'consumer_name': self.name
                }
                await get_stream_queue_manager().produce(
                    self.config.dead_letter_stream,
                    dead_letter_data
                )
                logger.info(f"Failed message {message.message_id} sent to dead letter stream {self.config.dead_letter_stream}")
            except Exception as e:
                logger.error(f"Failed to send message to dead letter stream: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get consumer statistics."""
        return {
            'name': self.name,
            'stream_name': self.stream_name,
            'processed_count': self._processed_count,
            'failed_count': self._failed_count,
            'is_running': self._is_running,
            'active_tasks': len([t for t in self._processing_tasks if not t.done()])
        }
    
    async def health_check(self) -> bool:
        """Perform health check on the consumer."""
        try:
            # Simple health check - can be extended with custom logic
            return self._is_running and all(
                not task.done() or task.exception() is None 
                for task in self._processing_tasks
            )
        except Exception as e:
            logger.error(f"Health check failed for consumer {self.name}: {e}")
            return False


class StreamQueueManager:
    """
    Redis Stream queue manager built on top of RedisManager.
    
    Provides comprehensive Stream operations including production,
    consumption, consumer management, and monitoring.
    """
    
    def __init__(self, redis_manager: 'RedisManager'):
        """
        Initialize Stream queue manager.
        
        :param redis_manager: RedisManager instance for Redis operations
        """
        self.redis_manager = redis_manager
        self._consumers: Dict[str, Dict[str, StreamConsumer]] = {}  # stream_name -> {consumer_name -> consumer}
        self._consumer_tasks: Dict[str, asyncio.Task] = {}  # task_key -> task
        self._monitor_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._is_initialized = False
        
    async def initialize(self) -> None:
        """Initialize the Stream queue manager."""
        if self._is_initialized:
            logger.warning("StreamQueueManager already initialized")
            return
            
        # Verify Redis connection
        await self.client.ping()
        self._is_initialized = True
        logger.info("StreamQueueManager initialized successfully")
    
    @property
    def client(self) -> Redis:
        """Get Redis client instance."""
        return self.redis_manager.client
    
    async def create_stream(self, stream_name: str, max_len: Optional[int] = None) -> bool:
        """
        Create a Stream if it doesn't exist.
        
        :param stream_name: Name of the Stream
        :param max_len: Optional maximum length for the Stream
        :return: True if Stream was created or already exists, False on error
        """
        try:
            # Create Stream by adding and immediately removing a temporary message
            temp_id = await self.client.xadd(
                stream_name, 
                {'_init': 'true'}, 
                maxlen=max_len or 0,
                approximate=True
            )
            await self.client.xdel(stream_name, temp_id)
            logger.info(f"Stream '{stream_name}' created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create Stream '{stream_name}': {e}")
            return False
    
    async def create_consumer_group(
        self, 
        stream_name: str, 
        group_name: str, 
        create_stream: bool = True
    ) -> bool:
        """
        Create a consumer group for a Stream.
        
        :param stream_name: Name of the Stream
        :param group_name: Name of the consumer group
        :param create_stream: Whether to create the Stream if it doesn't exist
        :return: True if consumer group was created or already exists, False on error
        """
        try:
            if create_stream and not await self.client.exists(stream_name):
                await self.create_stream(stream_name)
            
            await self.client.xgroup_create(
                stream_name, 
                group_name, 
                id='$',  # Start from latest message
                mkstream=True  # Create Stream if it doesn't exist
            )
            logger.info(f"Consumer group '{group_name}' created for Stream '{stream_name}'")
            return True
            
        except ResponseError as e:
            if "BUSYGROUP" in str(e):
                logger.info(f"Consumer group '{group_name}' already exists for Stream '{stream_name}'")
                return True
            else:
                logger.error(f"Failed to create consumer group '{group_name}': {e}")
                return False
        except Exception as e:
            logger.error(f"Error creating consumer group '{group_name}': {e}")
            return False
    
    async def produce(
        self, 
        stream_name: str, 
        message_data: Dict[str, Any], 
        max_len: Optional[int] = None
    ) -> Optional[str]:
        """
        Produce a message to a Stream.
        
        :param stream_name: Name of the target Stream
        :param message_data: Message data as key-value pairs
        :param max_len: Optional maximum Stream length
        :return: Message ID if successful, None otherwise
        """
        try:
            args = []
            if max_len:
                args.extend(['MAXLEN', '~', max_len])
            
            message_id = await self.client.xadd(
                stream_name, 
                message_data, 
                id='*',
                *args
            )
            logger.debug(f"Message produced successfully: Stream={stream_name}, ID={message_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"Failed to produce message to Stream '{stream_name}': {e}")
            return None
    
    async def batch_produce(
        self, 
        stream_name: str, 
        messages: List[Dict[str, Any]], 
        max_len: Optional[int] = None
    ) -> List[Optional[str]]:
        """
        Produce multiple messages to a Stream in batch.
        
        :param stream_name: Name of the target Stream
        :param messages: List of message data dictionaries
        :param max_len: Optional maximum Stream length
        :return: List of message IDs (None for failed messages)
        """
        pipeline = self.client.pipeline()
        
        for message_data in messages:
            args = [stream_name, message_data]
            if max_len:
                args.extend(['MAXLEN', '~', max_len])
            pipeline.xadd(*args)
        
        try:
            results = await pipeline.execute()
            logger.debug(f"Batch produced {len(messages)} messages to Stream '{stream_name}'")
            return results
        except Exception as e:
            logger.error(f"Failed to batch produce messages to Stream '{stream_name}': {e}")
            return [None] * len(messages)
    
    def register_consumer(
        self, 
        stream_name: str, 
        consumer_name: str, 
        consumer: StreamConsumer
    ) -> None:
        """
        Register a consumer for a Stream.
        
        :param stream_name: Name of the Stream
        :param consumer_name: Unique name for the consumer
        :param consumer: Consumer instance
        """
        if stream_name not in self._consumers:
            self._consumers[stream_name] = {}
        
        if consumer_name in self._consumers[stream_name]:
            logger.warning(f"Consumer '{consumer_name}' already registered for Stream '{stream_name}', overwriting")
        
        self._consumers[stream_name][consumer_name] = consumer
        logger.info(f"Consumer '{consumer_name}' registered for Stream '{stream_name}'")
    
    async def start_consumer(
        self, 
        stream_name: str, 
        consumer_name: str, 
        group_name: str,
        config: Optional[ConsumerConfig] = None
    ) -> bool:
        """
        Start a registered consumer.
        
        :param stream_name: Name of the Stream
        :param consumer_name: Name of the consumer
        :param group_name: Name of the consumer group
        :param config: Optional consumer configuration
        :return: True if consumer started successfully, False otherwise
        """
        if stream_name not in self._consumers or consumer_name not in self._consumers[stream_name]:
            logger.error(f"Consumer '{consumer_name}' not registered for Stream '{stream_name}'")
            return False
        
        consumer = self._consumers[stream_name][consumer_name]
        consumer_config = config or consumer.config
        
        # Ensure consumer group exists
        if not await self.create_consumer_group(stream_name, group_name):
            return False
        
        # Create consumption task
        task_key = f"{stream_name}:{consumer_name}:{group_name}"
        if task_key in self._consumer_tasks and not self._consumer_tasks[task_key].done():
            logger.warning(f"Consumer task '{task_key}' is already running")
            return True
        
        task = asyncio.create_task(
            self._consume_loop(stream_name, group_name, consumer_name, consumer_config)
        )
        self._consumer_tasks[task_key] = task
        
        logger.info(f"Consumer '{consumer_name}' started (Stream: {stream_name}, Group: {group_name})")
        return True
    
    async def _consume_loop(
        self, 
        stream_name: str, 
        group_name: str, 
        consumer_name: str,
        config: ConsumerConfig
    ) -> None:
        """
        Main consumption loop for a consumer.
        
        :param stream_name: Name of the Stream
        :param group_name: Name of the consumer group
        :param consumer_name: Name of the consumer
        :param config: Consumer configuration
        """
        consumer = self._consumers[stream_name][consumer_name]
        consumer._is_running = True
        
        logger.info(f"Starting consumption loop: Stream={stream_name}, Group={group_name}, Consumer={consumer_name}")
        
        while consumer._is_running:
            try:
                # Read messages from Stream
                results = await self.client.xreadgroup(
                    group_name, consumer_name,
                    streams={stream_name: '>'},  # '>' means only new messages
                    count=config.batch_size,
                    block=config.block_time_ms
                )
                
                if not results:
                    continue
                
                # Process message batch
                for stream_key, messages in results:
                    for message_id, fields in messages:
                        stream_message = StreamMessage(
                            message_id=message_id,
                            fields=fields,
                            stream_name=stream_name,
                            consumer_group=group_name,
                            consumer_name=consumer_name
                        )
                        
                        # Process message
                        processing_task = asyncio.create_task(
                            self._process_single_message(consumer, stream_message, config)
                        )
                        consumer._processing_tasks.append(processing_task)
                        
                        # Clean up completed tasks
                        consumer._processing_tasks = [
                            task for task in consumer._processing_tasks 
                            if not task.done()
                        ]
                        
            except Exception as e:
                logger.error(f"Error in consumption loop: {e}")
                await asyncio.sleep(1)  # Brief pause on error
    
    async def _process_single_message(
        self, 
        consumer: StreamConsumer, 
        message: StreamMessage,
        config: ConsumerConfig
    ) -> None:
        """
        Process a single message with error handling.
        
        :param consumer: Consumer instance
        :param message: Message to process
        :param config: Consumer configuration
        """
        try:
            success = await consumer.on_message(message)
            
            # Acknowledge message if processing succeeded and auto-ack is disabled
            if success and not config.auto_ack:
                await self.ack_message(
                    message.stream_name,
                    message.consumer_group,
                    message.message_id
                )
                
        except Exception as e:
            logger.error(f"Unhandled error processing message {message.message_id}: {e}")
    
    async def ack_message(self, stream_name: str, group_name: str, message_id: str) -> bool:
        """
        Acknowledge a processed message.
        
        :param stream_name: Name of the Stream
        :param group_name: Name of the consumer group
        :param message_id: ID of the message to acknowledge
        :return: True if acknowledgement succeeded, False otherwise
        """
        try:
            await self.client.xack(stream_name, group_name, message_id)
            logger.debug(f"Message acknowledged successfully: {message_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to acknowledge message {message_id}: {e}")
            return False
    
    async def get_stream_info(self, stream_name: str) -> Dict[str, Any]:
        """
        Get information about a Stream.
        
        :param stream_name: Name of the Stream
        :return: Dictionary containing Stream information
        """
        try:
            info = await self.client.xinfo_stream(stream_name)
            info['length'] = await self.client.xlen(stream_name)
            return info
        except Exception as e:
            logger.error(f"Failed to get Stream info for '{stream_name}': {e}")
            return {}
    
    async def get_pending_messages(
        self, 
        stream_name: str, 
        group_name: str,
        consumer_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get pending messages for a consumer group.
        
        :param stream_name: Name of the Stream
        :param group_name: Name of the consumer group
        :param consumer_name: Optional specific consumer name
        :return: List of pending messages
        """
        try:
            pending_info = await self.client.xpending(stream_name, group_name)
            if pending_info['pending'] == 0:
                return []
            
            pending_msgs = await self.client.xpending_range(
                stream_name, group_name, 
                min='-', max='+', count=100,
                consumername=consumer_name
            )
            return pending_msgs
        except Exception as e:
            logger.error(f"Failed to get pending messages: {e}")
            return []
    
    async def claim_abandoned_messages(
        self, 
        stream_name: str, 
        group_name: str, 
        consumer_name: str,
        min_idle_time: int = 60000
    ) -> List[str]:
        """
        Claim messages that have been idle for too long.
        
        :param stream_name: Name of the Stream
        :param group_name: Name of the consumer group
        :param consumer_name: Name of the consumer claiming messages
        :param min_idle_time: Minimum idle time in milliseconds
        :return: List of claimed message IDs
        """
        try:
            # Get abandoned messages
            abandoned = await self.client.xpending_range(
                stream_name, group_name, '-', '+', 100,
                idle=min_idle_time
            )
            
            if not abandoned:
                return []
            
            # Claim messages
            message_ids = [msg['message_id'] for msg in abandoned]
            claimed = await self.client.xclaim(
                stream_name, group_name, consumer_name, min_idle_time,
                message_ids
            )
            
            claimed_ids = [msg[0] for msg in claimed] if claimed else []
            logger.info(f"Claimed {len(claimed_ids)} abandoned messages")
            return claimed_ids
            
        except Exception as e:
            logger.error(f"Failed to claim abandoned messages: {e}")
            return []
    
    async def start_monitor(self, interval: int = 30) -> None:
        """
        Start monitoring task for Stream queues.
        
        :param interval: Monitoring interval in seconds
        """
        if self._monitor_task and not self._monitor_task.done():
            logger.warning("Monitor task is already running")
            return
        
        self._monitor_task = asyncio.create_task(self._monitor_loop(interval))
        logger.info(f"Stream queue monitor started with interval: {interval} seconds")
    
    async def _monitor_loop(self, interval: int) -> None:
        """Main monitoring loop."""
        while True:
            try:
                await self._collect_metrics()
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(interval)
    
    async def _collect_metrics(self) -> None:
        """Collect and log monitoring metrics."""
        metrics = {
            'timestamp': asyncio.get_event_loop().time(),
            'streams': {},
            'consumers': {
                'running_tasks': len([t for t in self._consumer_tasks.values() if not t.done()]),
                'registered_consumers': sum(len(consumers) for consumers in self._consumers.values())
            }
        }
        
        # Collect metrics for each Stream
        for stream_name in self._consumers.keys():
            try:
                stream_info = await self.get_stream_info(stream_name)
                if stream_info:
                    metrics['streams'][stream_name] = {
                        'message_count': stream_info.get('length', 0),
                        'last_id': stream_info.get('last-generated-id', 'unknown')
                    }
            except Exception as e:
                logger.debug(f"Failed to collect metrics for Stream '{stream_name}': {e}")
        
        logger.info(f"Stream queue metrics: {metrics}")
    
    async def start_health_checks(self, interval: int = 30) -> None:
        """
        Start health check task for all consumers.
        
        :param interval: Health check interval in seconds
        """
        if self._health_check_task and not self._health_check_task.done():
            logger.warning("Health check task is already running")
            return
        
        self._health_check_task = asyncio.create_task(self._health_check_loop(interval))
        logger.info(f"Consumer health checks started with interval: {interval} seconds")
    
    async def _health_check_loop(self, interval: int) -> None:
        """Health check loop for all consumers."""
        while True:
            try:
                for stream_name, consumers in self._consumers.items():
                    for consumer_name, consumer in consumers.items():
                        is_healthy = await consumer.health_check()
                        if not is_healthy:
                            logger.warning(f"Consumer '{consumer_name}' for Stream '{stream_name}' is unhealthy")
                
                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(interval)
    
    def get_consumer_stats(self) -> Dict[str, Any]:
        """Get statistics for all consumers."""
        stats = {}
        for stream_name, consumers in self._consumers.items():
            stats[stream_name] = {
                consumer_name: consumer.get_stats()
                for consumer_name, consumer in consumers.items()
            }
        return stats
    
    async def stop_consumer(
        self, 
        stream_name: str, 
        consumer_name: str, 
        group_name: str
    ) -> bool:
        """
        Stop a specific consumer.
        
        :param stream_name: Name of the Stream
        :param consumer_name: Name of the consumer
        :param group_name: Name of the consumer group
        :return: True if consumer was stopped, False otherwise
        """
        task_key = f"{stream_name}:{consumer_name}:{group_name}"
        
        if task_key not in self._consumer_tasks:
            logger.warning(f"No running consumer task found for key: {task_key}")
            return False
        
        # Stop the consumer
        if stream_name in self._consumers and consumer_name in self._consumers[stream_name]:
            self._consumers[stream_name][consumer_name]._is_running = False
        
        # Cancel the task
        task = self._consumer_tasks[task_key]
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        del self._consumer_tasks[task_key]
        logger.info(f"Consumer '{consumer_name}' stopped (Stream: {stream_name}, Group: {group_name})")
        return True
    
    async def stop_all_consumers(self) -> None:
        """Stop all running consumers."""
        # Stop all consumers
        for stream_name, consumers in self._consumers.items():
            for consumer in consumers.values():
                consumer._is_running = False
        
        # Cancel all consumer tasks
        for task_key, task in self._consumer_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self._consumer_tasks.clear()
        logger.info("All consumers stopped")
    
    async def stop_monitor(self) -> None:
        """Stop the monitoring task."""
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
            logger.info("Monitor task stopped")
    
    async def stop_health_checks(self) -> None:
        """Stop the health check task."""
        if self._health_check_task and not self._health_check_task.done():
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None
            logger.info("Health check task stopped")
    
    async def close(self) -> None:
        """Close the Stream queue manager and release resources."""
        await self.stop_all_consumers()
        await self.stop_monitor()
        await self.stop_health_checks()
        self._is_initialized = False
        logger.info("StreamQueueManager closed")


_stream_queue_manager: Optional[StreamQueueManager] = None


async def init_stream_queue_manager(redis_manager: 'RedisManager') -> StreamQueueManager:
    """
    Initialize the global Stream queue manager.
    
    :param redis_manager: RedisManager instance
    :return: Initialized StreamQueueManager instance
    """
    global _stream_queue_manager
    _stream_queue_manager = StreamQueueManager(redis_manager)
    await _stream_queue_manager.initialize()
    return _stream_queue_manager


def get_stream_queue_manager() -> StreamQueueManager:
    """
    Get the global Stream queue manager instance.
    
    :return: StreamQueueManager instance
    :raises RuntimeError: If manager is not initialized
    """
    if _stream_queue_manager is None:
        raise RuntimeError("StreamQueueManager not initialized. Call init_stream_queue_manager first.")
    return _stream_queue_manager


def stream_consumer(stream_name: str, consumer_name: str, config: ConsumerConfig = None):
    """
    Decorator for creating Stream consumers from functions.
    
    :param stream_name: Name of the Stream
    :param consumer_name: Name of the consumer
    :param config: Consumer configuration
    :return: Decorator function
    """
    def decorator(process_func: Callable[[StreamMessage], Any]):
        class DecoratedConsumer(StreamConsumer):
            async def process_message(self, message: StreamMessage) -> bool:
                return await process_func(message)
        
        consumer = DecoratedConsumer(consumer_name, stream_name, config)
        get_stream_queue_manager().register_consumer(stream_name, consumer_name, consumer)
        return consumer
    
    return decorator
