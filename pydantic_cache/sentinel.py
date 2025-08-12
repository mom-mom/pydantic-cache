"""Sentinel values for cache operations."""


class _CacheMiss:
    """Sentinel class to represent a cache miss."""

    def __repr__(self) -> str:
        return "<CacheMiss>"

    def __bool__(self) -> bool:
        return False


# Singleton sentinel instance
CACHE_MISS = _CacheMiss()
