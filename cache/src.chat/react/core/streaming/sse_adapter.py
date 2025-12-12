"""Module definition"""

import json
import asyncio
from typing import AsyncIterator, Any

from .stream import AsyncOutputStream


class SSEAdapter(AsyncOutputStream):
    """SSE - SSE"""

    def __init__(self):
        self.stream_queue = asyncio.Queue()
        self.closed = False

    async def send(self, event_type: str, data: Any):
        """SSE"""
        if self.closed:
            return

        #  -> JSON
        if event_type in ["tool-call", "tool-result", "metadata"]:
            data_str = json.dumps(data, ensure_ascii=False)
        else:
            #  -> 
            data_str = str(data)

        sse_event = f"event: {event_type}\ndata: {data_str}\n\n"
        await self.stream_queue.put(sse_event)

    async def flush(self):
        """Module definition"""
        pass

    async def close(self):
        """Module definition"""
        self.closed = True

    async def stream_generator(self) -> AsyncIterator[str]:
        """SSE"""
        while not self.closed or not self.stream_queue.empty():
            try:
                event = await asyncio.wait_for(
                    self.stream_queue.get(),
                    timeout=1.0
                )
                yield event
            except asyncio.TimeoutError:
                continue

    def is_closed(self) -> bool:
        """Module definition"""
        return self.closed
