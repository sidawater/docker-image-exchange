import asyncio
import logging
from init.db.redis.stream import (
    StreamConsumer,
    StreamMessage,
    ConsumerConfig,
    stream_consumer,
    init_stream_queue_manager,
    get_stream_queue_manager
)
from init.db.redis.client import redis_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderProcessingConsumer(StreamConsumer):
    """Consumer for processing order messages."""
    
    async def process_message(self, message: StreamMessage) -> bool:
        """Process order message."""
        try:
            order_data = message.fields
            logger.info(f"Processing order: "
                        f"ID={order_data.get('order_id')}, "
                        f"Amount={order_data.get('amount')}")
            
            # Simulate business processing
            await asyncio.sleep(0.5)
            # Simulate successful processing
            return True
            
        except Exception as e:
            logger.error(f"Order processing failed: {e}")
            return False


# Example 2: Using decorator for consumer creation
@stream_consumer(
    stream_name="notification_stream",
    consumer_name="email_notifier",
    config=ConsumerConfig(batch_size=5, max_retries=2)
)
async def handle_notification(message: StreamMessage) -> bool:
    """Process notification message."""
    notification_data = message.fields
    logger.info(f"Sending notification: "
                f"Type={notification_data.get('type')}, "
                f"Target={notification_data.get('target')}")
    await asyncio.sleep(0.2)
    return True


async def demo_stream_queues():
    """Demonstrate Stream queue usage."""
    
    # 1. Initialize Redis manager
    logger.info("Redis manager initialized successfully")
    
    # 2. Initialize Stream queue manager
    await init_stream_queue_manager(redis_manager)
    stream_mgr = get_stream_queue_manager()
    
    try:
        # 3. Create consumer instance and register
        order_consumer = OrderProcessingConsumer(
            name="order_processor",
            stream_name="order_stream",
            config=ConsumerConfig(
                batch_size=10,
                max_retries=3,
                dead_letter_stream="dead_letter_orders"
            )
        )
        stream_mgr.register_consumer("order_stream", "order_processor", order_consumer)
        
        # 4. Create Stream and consumer group
        await stream_mgr.create_stream("order_stream", max_len=1000)
        await stream_mgr.create_consumer_group("order_stream", "order_processing_group")
        
        # 5. Start consumer
        await stream_mgr.start_consumer(
            "order_stream", 
            "order_processor", 
            "order_processing_group"
        )
        
        # 6. Produce test messages
        for i in range(20):
            order_message = {
                "order_id": f"ORD_{i:06d}",
                "user_id": f"USER_{i % 5}",
                "amount": str(100 + i * 10),
                "timestamp": str(asyncio.get_event_loop().time())
            }
            await stream_mgr.produce("order_stream", order_message)
            await asyncio.sleep(0.1)
        
        # 7. Start monitoring and health checks
        await stream_mgr.start_monitor(interval=10)
        await stream_mgr.start_health_checks(interval=15)
        
        # 8. Run for some time
        logger.info("Stream queue system running...")
        await asyncio.sleep(30)
        
        # 9. Check Stream information
        stream_info = await stream_mgr.get_stream_info("order_stream")
        logger.info(f"Order Stream info: {stream_info}")
        
        # 10. Check pending messages
        pending_messages = await stream_mgr.get_pending_messages(
            "order_stream", "order_processing_group"
        )
        logger.info(f"Pending messages count: {len(pending_messages)}")
        
        # 11. Get consumer statistics
        consumer_stats = stream_mgr.get_consumer_stats()
        logger.info(f"Consumer statistics: {consumer_stats}")
        
    finally:
        # Clean up resources
        await stream_mgr.close()
        await redis_manager.close()


async def advanced_demo():
    """Advanced usage demonstration - multiple Streams and consumers."""
    
    await redis_manager.init('redis://localhost:6379/0')
    await init_stream_queue_manager(redis_manager)
    stream_mgr = get_stream_queue_manager()
    
    try:
        # Define multiple consumers
        consumers = [
            {
                'name': 'inventory_updater',
                'stream': 'inventory_stream', 
                'group': 'inventory_group',
                'config': ConsumerConfig(batch_size=5)
            },
            {
                'name': 'payment_processor', 
                'stream': 'payment_stream',
                'group': 'payment_group',
                'config': ConsumerConfig(batch_size=3, max_retries=2)
            }
        ]
        
        # Register and start all consumers
        for consumer_info in consumers:
            consumer = StreamConsumer(
                name=consumer_info['name'],
                stream_name=consumer_info['stream'],
                config=consumer_info['config']
            )
            
            stream_mgr.register_consumer(
                consumer_info['stream'], 
                consumer_info['name'], 
                consumer
            )
            
            await stream_mgr.create_consumer_group(
                consumer_info['stream'], 
                consumer_info['group']
            )
            
            await stream_mgr.start_consumer(
                consumer_info['stream'],
                consumer_info['name'],
                consumer_info['group']
            )
        
        # Produce messages to multiple Streams
        inventory_tasks = []
        payment_tasks = []
        
        for i in range(10):
            inventory_task = stream_mgr.produce("inventory_stream", {
                "product_id": f"PROD_{i}",
                "action": "update",
                "quantity": str(i * 10)
            })
            inventory_tasks.append(inventory_task)
            
            payment_task = stream_mgr.produce("payment_stream", {
                "payment_id": f"PAY_{i}",
                "amount": str(50 + i * 5),
                "currency": "USD"
            })
            payment_tasks.append(payment_task)
        
        # Wait for all messages to be produced
        await asyncio.gather(*inventory_tasks, *payment_tasks)
        
        # Start monitoring and run
        await stream_mgr.start_monitor(interval=15)
        await stream_mgr.start_health_checks(interval=20)
        await asyncio.sleep(60)
        
    finally:
        await stream_mgr.close()
        await redis_manager.close()


if __name__ == "__main__":
    # Run demonstration
    asyncio.run(demo_stream_queues())
    
    # Run advanced demonstration
    # asyncio.run(advanced_demo())