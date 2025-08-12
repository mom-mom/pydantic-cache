import pytest_asyncio

from pydantic_cache import PydanticCache
from pydantic_cache.backends.inmemory import InMemoryBackend


@pytest_asyncio.fixture
async def inmemory_backend():
    """Fixture for in-memory backend."""
    backend = InMemoryBackend()
    yield backend
    # Cleanup
    await backend.clear()


@pytest_asyncio.fixture
async def cache_setup(inmemory_backend):
    """Setup cache with in-memory backend."""
    PydanticCache.init(inmemory_backend, prefix="test", expire=60, enable=True)
    yield
    # Cleanup
    await PydanticCache.clear()
    PydanticCache._backend = None
