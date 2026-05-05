import time
from typing import Any, Optional

class SimpleCache:
    def __init__(self):
        self._store = {}

    def get(self, key: str) -> Optional[Any]:
        item = self._store.get(key)
        if not item:
            return None
        expires_at, value = item
        if expires_at and expires_at < time.time():
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: int = 60):
        expires_at = time.time() + ttl if ttl else None
        self._store[key] = (expires_at, value)

cache = SimpleCache()
