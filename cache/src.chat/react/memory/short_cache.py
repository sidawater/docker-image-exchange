"""Short-term Cache"""

import time
from typing import Any, Optional


class ShortTermCache:
    """Short-term Cache"""

    def __init__(self, ttl: int = 300) -> None:
        self.ttl = ttl
        self._cache: dict = {}

    def get(self, key: str) -> Optional[Any]:
        """Get cache"""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Set cache"""
        self._cache[key] = (value, time.time())

    def clear(self) -> None:
        """Clear cache"""
        self._cache.clear()
