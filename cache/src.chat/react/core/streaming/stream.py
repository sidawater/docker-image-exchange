"""Async Output Stream"""

import asyncio
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class AsyncOutputStream(ABC):
    """Async output stream base class"""

    @abstractmethod
    async def send(self, event_type: str, data: Any):
        """Send event"""
        pass

    @abstractmethod
    async def flush(self):
        """Flush stream"""
        pass

    @abstractmethod
    async def close(self):
        """Close stream"""
        pass


class TextStream(AsyncOutputStream):
    """Text stream - for thinking and content"""

    def __init__(self, output_stream: Optional[AsyncOutputStream] = None):
        self.output = output_stream or NullStream()
        self.buffer = ""
        self.is_closed = False

    async def send_text(self, text: str):
        """Stream send text"""
        if self.is_closed:
            return
        self.buffer += text
        await self.output.send("content", text)

    async def send_thinking(self, text: str):
        """Stream send thinking process"""
        if self.is_closed:
            return
        await self.output.send("thinking", text)

    async def send_metadata(self, metadata: Dict):
        """Send metadata"""
        if self.is_closed:
            return
        await self.output.send("metadata", metadata)

    async def send_tool_call(self, tool_call: Dict):
        """Send tool call (complete structured data)"""
        if self.is_closed:
            return
        await self.output.send("tool-call", tool_call)

    async def send_tool_result(self, result: Dict):
        """Send tool result (complete structured data)"""
        if self.is_closed:
            return
        await self.output.send("tool-result", result)

    async def send_error(self, error: str):
        """Send error"""
        if self.is_closed:
            return
        await self.output.send("error", error)

    async def send_status(self, status: str):
        """Send status"""
        if self.is_closed:
            return
        await self.output.send("status", status)

    async def send(self, event_type: str, data: Any):
        """Send event (general interface)"""
        if self.is_closed:
            return
        await self.output.send(event_type, data)

    async def flush(self):
        """Flush stream"""
        if hasattr(self.output, 'flush'):
            await self.output.flush()

    async def close(self):
        """Close stream"""
        self.is_closed = True
        if hasattr(self.output, 'close'):
            await self.output.close()

    def get_buffer(self) -> str:
        """Get buffer content"""
        return self.buffer


class NullStream(AsyncOutputStream):
    """Null stream implementation - for testing or disabling output"""

    async def send(self, event_type: str, data: Any):
        """Null implementation"""
        pass

    async def flush(self):
        """Null implementation"""
        pass

    async def close(self):
        """Null implementation"""
        pass

    # Provide null implementation for methods provided by TextStream
    async def send_text(self, text: str):
        """Null implementation"""
        pass

    async def send_thinking(self, text: str):
        """Null implementation"""
        pass

    async def send_metadata(self, metadata: Dict):
        """Null implementation"""
        pass

    async def send_tool_call(self, tool_call: Dict):
        """Null implementation"""
        pass

    async def send_tool_result(self, result: Dict):
        """Null implementation"""
        pass

    async def send_error(self, error: str):
        """Null implementation"""
        pass

    async def send_status(self, status: str):
        """Null implementation"""
        pass


class QueueStream(AsyncOutputStream):
    """Queue stream - puts events into queue"""

    def __init__(self, maxsize: int = 100):
        self.queue = asyncio.Queue(maxsize=maxsize)
        self.is_closed = False

    async def send(self, event_type: str, data: Any):
        """Send event to queue"""
        if self.is_closed:
            return

        # Convert structured data to JSON string
        if event_type in ["tool-call", "tool-result", "metadata"]:
            data_str = json.dumps(data, ensure_ascii=False)
        else:
            # Non-structured data directly converted to string
            data_str = str(data)

        event = {
            "event": event_type,
            "data": data_str
        }

        try:
            self.queue.put_nowait(event)
        except asyncio.QueueFull:
            # When queue is full, discard oldest event
            try:
                self.queue.get_nowait()
                self.queue.put_nowait(event)
            except asyncio.QueueEmpty:
                pass

    async def flush(self):
        """Null implementation"""
        pass

    async def close(self):
        """Close stream"""
        self.is_closed = True

    async def get_event(self) -> Optional[Dict]:
        """Get event from queue"""
        try:
            return await asyncio.wait_for(self.queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            return None

    def is_queue_empty(self) -> bool:
        """Check if queue is empty"""
        return self.queue.empty()
