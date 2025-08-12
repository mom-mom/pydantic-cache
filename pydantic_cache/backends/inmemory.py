import time
from typing import Any

from pydantic_cache.sentinel import CACHE_MISS
from pydantic_cache.types import Backend


class InMemoryBackend(Backend):
    """Simple in-memory cache backend for testing and development."""

    def __init__(self):
        self._cache: dict[str, tuple[bytes, float | None]] = {}

    async def get_with_ttl(self, key: str) -> tuple[int, bytes | Any]:
        if key not in self._cache:
            return 0, CACHE_MISS

        value, expire_time = self._cache[key]

        if expire_time is None:
            return -1, value

        current_time = time.time()
        if current_time >= expire_time:
            del self._cache[key]
            return 0, CACHE_MISS

        ttl = int(expire_time - current_time)
        return ttl, value

    async def get(self, key: str) -> bytes | None:
        _, value = await self.get_with_ttl(key)
        # Convert CACHE_MISS to None for backward compatibility
        if value is CACHE_MISS:
            return None
        return value

    async def set(self, key: str, value: bytes, expire: int | None = None) -> None:
        expire_time = None
        if expire is not None:
            expire_time = time.time() + expire
        self._cache[key] = (value, expire_time)

    async def clear(self, namespace: str | None = None, key: str | None = None) -> int:
        if key:
            if key in self._cache:
                del self._cache[key]
                return 1
            return 0

        if namespace:
            keys_to_delete = [k for k in self._cache if k.startswith(f"{namespace}:")]
            for k in keys_to_delete:
                del self._cache[k]
            return len(keys_to_delete)

        count = len(self._cache)
        self._cache.clear()
        return count
