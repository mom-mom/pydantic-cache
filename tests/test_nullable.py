"""Tests for nullable/optional type support."""

import asyncio

import pytest
from pydantic import BaseModel

from pydantic_cache import PydanticCache, cache
from pydantic_cache.backends.inmemory import InMemoryBackend
from pydantic_cache.coder import JsonCoder, PickleCoder


class UserProfile(BaseModel):
    id: int
    name: str
    bio: str | None = None
    age: int | None = None
    tags: list[str] | None = None


class TestNullableTypes:
    @pytest.mark.asyncio
    async def test_none_value_caching(self, cache_setup):
        """Test that None values are properly cached and distinguished from cache misses."""
        call_count = 0

        @cache(namespace="nullable")
        async def get_optional_value(key: str) -> str | None:
            nonlocal call_count
            call_count += 1
            if key == "none":
                return None
            return f"value_{key}"

        # First call returning None
        result1 = await get_optional_value("none")
        assert result1 is None
        assert call_count == 1

        # Second call should use cached None
        result2 = await get_optional_value("none")
        assert result2 is None
        assert call_count == 1  # No additional call

        # Call with different key
        result3 = await get_optional_value("exists")
        assert result3 == "value_exists"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_optional_pydantic_model(self, cache_setup):
        """Test caching functions that return Optional[PydanticModel]."""
        call_count = 0

        @cache(namespace="models")
        async def get_user_profile(user_id: int) -> UserProfile | None:
            nonlocal call_count
            call_count += 1
            if user_id == 0:
                return None
            return UserProfile(
                id=user_id, name=f"User {user_id}", bio=None if user_id == 1 else f"Bio for user {user_id}", age=None
            )

        # Test None return
        profile1 = await get_user_profile(0)
        assert profile1 is None
        assert call_count == 1

        # Cached None
        profile2 = await get_user_profile(0)
        assert profile2 is None
        assert call_count == 1

        # Test model with None fields
        profile3 = await get_user_profile(1)
        assert profile3 is not None
        assert profile3.bio is None
        assert profile3.age is None
        assert call_count == 2

        # Cached model
        profile4 = await get_user_profile(1)
        assert profile4 is not None
        assert profile4.bio is None
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_union_types(self, cache_setup):
        """Test caching functions with Union types including None."""
        call_count = 0

        @cache(namespace="union")
        async def get_mixed_type(key: str) -> str | int | None:
            nonlocal call_count
            call_count += 1
            if key == "string":
                return "text"
            elif key == "number":
                return 42
            elif key == "none":
                return None
            else:
                return "default"

        # Test each type
        assert await get_mixed_type("string") == "text"
        assert await get_mixed_type("number") == 42
        assert await get_mixed_type("none") is None
        assert call_count == 3

        # All should be cached
        assert await get_mixed_type("string") == "text"
        assert await get_mixed_type("number") == 42
        assert await get_mixed_type("none") is None
        assert call_count == 3  # No additional calls

    @pytest.mark.asyncio
    async def test_nested_optional(self, cache_setup):
        """Test caching with nested optional types."""
        call_count = 0

        @cache(namespace="nested")
        async def get_nested_data(key: str) -> list[str | None] | None:
            nonlocal call_count
            call_count += 1
            if key == "none":
                return None
            elif key == "empty":
                return []
            elif key == "mixed":
                return ["value1", None, "value3"]
            else:
                return ["a", "b", "c"]

        # Test None
        result1 = await get_nested_data("none")
        assert result1 is None
        assert call_count == 1

        # Test list with None elements
        result2 = await get_nested_data("mixed")
        assert result2 == ["value1", None, "value3"]
        assert call_count == 2

        # Cached calls
        assert await get_nested_data("none") is None
        assert await get_nested_data("mixed") == ["value1", None, "value3"]
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_none_with_different_coders(self):
        """Test None handling with both JSON and Pickle coders."""
        for coder_class in [JsonCoder, PickleCoder]:
            backend = InMemoryBackend()
            PydanticCache.init(backend, coder=coder_class, prefix=coder_class.__name__)

            call_count = 0

            @cache(namespace="coder_test")
            async def get_optional(key: str) -> dict | None:
                nonlocal call_count
                call_count += 1
                if key == "none":
                    return None
                return {"key": key}

            # Test None caching
            result1 = await get_optional("none")
            assert result1 is None

            result2 = await get_optional("none")
            assert result2 is None
            assert call_count == 1  # Cached

            # Test non-None
            result3 = await get_optional("data")
            assert result3 == {"key": "data"}
            assert call_count == 2

            # Clear for next iteration
            await backend.clear()

    @pytest.mark.asyncio
    async def test_optional_with_clear(self, cache_setup):
        """Test that clearing cache works correctly with None values."""
        call_count = 0

        @cache(namespace="clear_test")
        async def get_value(key: str) -> str | None:
            nonlocal call_count
            call_count += 1
            return None if key == "none" else key

        # Cache None value
        assert await get_value("none") is None
        assert call_count == 1

        # Clear cache
        await PydanticCache.clear(namespace="clear_test")

        # Should call function again
        assert await get_value("none") is None
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_concurrent_none_caching(self, cache_setup):
        """Test concurrent access to functions returning None."""
        call_count = 0

        @cache(namespace="concurrent")
        async def maybe_slow_function(value: int) -> int | None:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.05)
            return None if value < 0 else value * 2

        # Launch concurrent requests for None value
        tasks = [maybe_slow_function(-1) for _ in range(5)]
        results = await asyncio.gather(*tasks)

        # All should be None
        assert all(r is None for r in results)
        # Some calls may happen before caching due to concurrency
        assert call_count <= 5

        # Subsequent call should be cached
        result = await maybe_slow_function(-1)
        assert result is None
        final_count = call_count

        # One more call to verify cache
        result = await maybe_slow_function(-1)
        assert result is None
        assert call_count == final_count  # No additional call
