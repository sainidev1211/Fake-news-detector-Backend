"""
utils/cache.py — simple in-memory LRU cache with TTL.
"""
import hashlib
import time
from collections import OrderedDict
from typing import Any, Optional

_MAX_SIZE = 200
_TTL = 600  # seconds


class _TTLCache:
    def __init__(self, max_size: int = _MAX_SIZE, ttl: int = _TTL):
        self._store: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl

    def _key(self, text: str) -> str:
        return hashlib.md5(text.strip().lower().encode()).hexdigest()

    def get(self, text: str) -> Optional[Any]:
        key = self._key(text)
        if key not in self._store:
            return None
        value, ts = self._store[key]
        if time.time() - ts > self._ttl:
            del self._store[key]
            return None
        # refresh position
        self._store.move_to_end(key)
        return value

    def set(self, text: str, value: Any) -> None:
        key = self._key(text)
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = (value, time.time())
        if len(self._store) > self._max_size:
            self._store.popitem(last=False)  # evict oldest

    def size(self) -> int:
        return len(self._store)

    def clear(self) -> None:
        self._store.clear()


# module-level singleton
cache = _TTLCache()
