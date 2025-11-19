import asyncio
import logging
from init.db.redis.stream import (
    StreamConsumer,
    StreamMessage,
)
from core.manager.knowledge import Knowledge
from core.manager.spliter import WordSpliter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderProcessingConsumer(StreamConsumer):
    """Consumer for processing order messages."""
    
    async def process_message(self, message: StreamMessage) -> bool:
        """Process order message."""
        order_data = message.fields
        logger.info(f"Processing order: "
                    f"ID={order_data.get('order_id')}, "
                    f"Amount={order_data.get('amount')}")
        
        await asyncio.sleep(0.5)
        return True
