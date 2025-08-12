import asyncio

import pytest
from pydantic import BaseModel

from pydantic_cache import PydanticCache, cache
from pydantic_cache.backends.inmemory import InMemoryBackend


class User(BaseModel):
    id: int
    name: str
    email: str
    age: int | None = None


class TestCacheDecorator:
    @pytest.mark.asyncio
    async def test_basic_caching(self, cache_setup):
        call_count = 0

        @cache(expire=60, namespace="test")
        async def get_user(user_id: int) -> User:
            nonlocal call_count
            call_count += 1
            return User(id=user_id, name=f"User {user_id}", email=f"user{user_id}@example.com", age=25)

        # First call - should execute function
        user1 = await get_user(1)
        assert call_count == 1
        assert user1.id == 1
        assert user1.name == "User 1"

        # Second call with same args - should use cache
        user2 = await get_user(1)
        assert call_count == 1  # Function not called again
        assert user1 == user2

        # Call with different args - should execute function
        user3 = await get_user(2)
        assert call_count == 2
        assert user3.id == 2

    @pytest.mark.asyncio
    async def test_cache_with_kwargs(self, cache_setup):
        call_count = 0

        @cache(namespace="search")
        async def search_users(query: str, limit: int = 10) -> list[str]:
            nonlocal call_count
            call_count += 1
            return [f"{query}_{i}" for i in range(limit)]

        # Test with different kwargs combinations
        result1 = await search_users("test", limit=5)
        assert call_count == 1
        assert len(result1) == 5

        # Same args - should use cache
        result2 = await search_users("test", limit=5)
        assert call_count == 1

        # Different kwargs - should execute
        result3 = await search_users("test", limit=10)
        assert call_count == 2
        assert len(result3) == 10

    @pytest.mark.asyncio
    async def test_sync_function_caching(self, cache_setup):
        call_count = 0

        @cache(namespace="compute")
        def compute_sum(x: int, y: int) -> int:
            nonlocal call_count
            call_count += 1
            return x + y

        # Sync function should be wrapped and made async
        result1 = await compute_sum(5, 3)
        assert result1 == 8
        assert call_count == 1

        # Second call should use cache
        result2 = await compute_sum(5, 3)
        assert result2 == 8
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_cache_disabled(self):
        backend = InMemoryBackend()
        PydanticCache.init(backend, enable=False)

        call_count = 0

        @cache(namespace="disabled")
        async def get_value() -> int:
            nonlocal call_count
            call_count += 1
            return 42

        # Should always execute when cache is disabled
        await get_value()
        await get_value()
        assert call_count == 2

        # Enable cache and test
        PydanticCache.set_enable(True)
        await get_value()  # This should execute and cache
        await get_value()  # This should use cache
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_cache_expiration(self, cache_setup):
        call_count = 0

        @cache(expire=1, namespace="expire")
        async def get_timestamp() -> float:
            nonlocal call_count
            call_count += 1
            return asyncio.get_event_loop().time()

        # First call
        time1 = await get_timestamp()
        assert call_count == 1

        # Immediate second call - should use cache
        time2 = await get_timestamp()
        assert call_count == 1
        assert time1 == time2

        # Wait for expiration
        await asyncio.sleep(1.1)

        # Should execute again after expiration
        time3 = await get_timestamp()
        assert call_count == 2
        assert time3 != time1

    @pytest.mark.asyncio
    async def test_cache_clear(self, cache_setup):
        call_count = 0

        @cache(namespace="users")
        async def get_user(user_id: int) -> str:
            nonlocal call_count
            call_count += 1
            return f"User {user_id}"

        # Cache some values
        await get_user(1)
        await get_user(2)
        assert call_count == 2

        # Verify cache is working
        await get_user(1)
        assert call_count == 2

        # Clear the namespace
        await PydanticCache.clear(namespace="users")

        # Should execute again after clear
        await get_user(1)
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_pydantic_model_caching(self, cache_setup):
        @cache(namespace="models")
        async def get_complex_user() -> User:
            return User(id=100, name="Complex User", email="complex@example.com", age=30)

        user1 = await get_complex_user()
        user2 = await get_complex_user()

        # Should be the same data
        assert user1.model_dump() == user2.model_dump()
        assert isinstance(user2, User)

    @pytest.mark.asyncio
    async def test_none_return_value(self, cache_setup):
        call_count = 0

        @cache(namespace="optional")
        async def maybe_get_user(user_id: int) -> User | None:
            nonlocal call_count
            call_count += 1
            if user_id < 0:
                return None
            return User(id=user_id, name="User", email="user@example.com")

        # Test caching None
        result1 = await maybe_get_user(-1)
        assert result1 is None
        assert call_count == 1

        result2 = await maybe_get_user(-1)
        assert result2 is None
        assert call_count == 1  # Should use cached None

        # Test caching actual value
        result3 = await maybe_get_user(1)
        assert result3 is not None
        assert result3.id == 1
        assert call_count == 2
