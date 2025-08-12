from pydantic_cache.coder import Coder, JsonCoder, OrjsonCoder, PickleCoder, PydanticJsonEncoder
from pydantic_cache.decorator import cache
from pydantic_cache.key_builder import default_key_builder
from pydantic_cache.types import Backend, KeyBuilder

__version__ = "1.0.0"

__all__ = [
    "Backend",
    "Coder",
    "JsonCoder",
    "KeyBuilder",
    "OrjsonCoder",
    "PickleCoder",
    "PydanticCache",
    "PydanticJsonEncoder",
    "cache",
    "default_key_builder",
]


class PydanticCache:
    _backend: Backend | None = None
    _prefix: str = ""
    _expire: int = 60
    _coder: Coder | type[Coder] = JsonCoder
    _key_builder: KeyBuilder = default_key_builder
    _enable: bool = True

    @classmethod
    def init(
        cls,
        backend: Backend,
        *,
        prefix: str = "",
        expire: int = 60,
        coder: type[Coder] | Coder | None = None,
        key_builder: KeyBuilder | None = None,
        enable: bool = True,
    ) -> None:
        """
        Initialize PydanticCache with a backend and configuration.

        Args:
            backend: Cache backend implementation
            prefix: Prefix for all cache keys
            expire: Default expiration time in seconds
            coder: Encoder/decoder for cache values (class or instance)
            key_builder: Function to build cache keys
            enable: Enable/disable caching globally
        """
        cls._backend = backend
        cls._prefix = prefix
        cls._expire = expire
        if coder is not None:
            cls._coder = coder
        if key_builder is not None:
            cls._key_builder = key_builder
        cls._enable = enable

    @classmethod
    def get_backend(cls) -> Backend:
        if cls._backend is None:
            raise RuntimeError("PydanticCache not initialized. Call PydanticCache.init() first.")
        return cls._backend

    @classmethod
    def get_prefix(cls) -> str:
        return cls._prefix

    @classmethod
    def get_expire(cls) -> int:
        return cls._expire

    @classmethod
    def get_coder(cls) -> Coder:
        # Return instance if already instantiated, or instantiate the class
        if isinstance(cls._coder, type):
            return cls._coder()
        return cls._coder

    @classmethod
    def get_key_builder(cls) -> KeyBuilder:
        return cls._key_builder

    @classmethod
    def get_enable(cls) -> bool:
        return cls._enable

    @classmethod
    def set_enable(cls, enable: bool) -> None:
        cls._enable = enable

    @classmethod
    async def clear(cls, namespace: str | None = None, key: str | None = None) -> int:
        """
        Clear cache entries.

        Args:
            namespace: Clear all keys in this namespace
            key: Clear a specific key

        Returns:
            Number of keys cleared
        """
        backend = cls.get_backend()
        # If namespace is provided, prepend the prefix
        if namespace:
            namespace = f"{cls._prefix}:{namespace}" if cls._prefix else namespace
        return await backend.clear(namespace=namespace, key=key)
