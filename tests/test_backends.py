import asyncio

import pytest

from pydantic_cache.backends.inmemory import InMemoryBackend
from pydantic_cache.sentinel import CACHE_MISS


class TestInMemoryBackend:
    @pytest.mark.asyncio
    async def test_set_and_get(self):
        backend = InMemoryBackend()

        # Test basic set and get
        await backend.set("key1", b"value1")
        value = await backend.get("key1")
        assert value == b"value1"

        # Test non-existent key
        value = await backend.get("nonexistent")
        assert value is None

    @pytest.mark.asyncio
    async def test_set_with_expiration(self):
        backend = InMemoryBackend()

        # Set with 1 second expiration
        await backend.set("key1", b"value1", expire=1)

        # Should exist immediately
        value = await backend.get("key1")
        assert value == b"value1"

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Should be expired
        value = await backend.get("key1")
        assert value is None

    @pytest.mark.asyncio
    async def test_get_with_ttl(self):
        backend = InMemoryBackend()

        # Test non-existent key
        ttl, value = await backend.get_with_ttl("nonexistent")
        assert ttl == 0
        assert value is CACHE_MISS

        # Test key without expiration
        await backend.set("key1", b"value1")
        ttl, value = await backend.get_with_ttl("key1")
        assert ttl == -1  # No expiration
        assert value == b"value1"

        # Test key with expiration
        await backend.set("key2", b"value2", expire=10)
        ttl, value = await backend.get_with_ttl("key2")
        assert 8 <= ttl <= 10  # Allow some time variance
        assert value == b"value2"

    @pytest.mark.asyncio
    async def test_clear_specific_key(self):
        backend = InMemoryBackend()

        await backend.set("key1", b"value1")
        await backend.set("key2", b"value2")

        # Clear specific key
        deleted = await backend.clear(key="key1")
        assert deleted == 1

        # key1 should be gone, key2 should remain
        assert await backend.get("key1") is None
        assert await backend.get("key2") == b"value2"

        # Clear non-existent key
        deleted = await backend.clear(key="nonexistent")
        assert deleted == 0

    @pytest.mark.asyncio
    async def test_clear_namespace(self):
        backend = InMemoryBackend()

        # Set keys with different namespaces
        await backend.set("users:1", b"user1")
        await backend.set("users:2", b"user2")
        await backend.set("products:1", b"product1")
        await backend.set("other", b"other")

        # Clear users namespace
        deleted = await backend.clear(namespace="users")
        assert deleted == 2

        # Users should be gone, others should remain
        assert await backend.get("users:1") is None
        assert await backend.get("users:2") is None
        assert await backend.get("products:1") == b"product1"
        assert await backend.get("other") == b"other"

    @pytest.mark.asyncio
    async def test_clear_all(self):
        backend = InMemoryBackend()

        await backend.set("key1", b"value1")
        await backend.set("key2", b"value2")
        await backend.set("key3", b"value3")

        # Clear all
        deleted = await backend.clear()
        assert deleted == 3

        # All keys should be gone
        assert await backend.get("key1") is None
        assert await backend.get("key2") is None
        assert await backend.get("key3") is None
