import pytest

from pydantic_cache import OrjsonCoder


class CustomId:
    """A custom ID type that's not JSON serializable by default."""

    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other):
        return isinstance(other, CustomId) and self.value == other.value


class CustomOrjsonCoder(OrjsonCoder):
    """Extended OrjsonCoder that handles CustomId objects."""

    @classmethod
    def _serialize_value(cls, value):
        # Handle CustomId objects
        if isinstance(value, CustomId):
            return str(value)

        # Handle nested structures with CustomId
        if isinstance(value, dict):
            return {k: cls._serialize_value(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [cls._serialize_value(item) for item in value]

        # Fall back to parent implementation
        return super()._serialize_value(value)

    @classmethod
    def decode(cls, value: bytes):
        # For this test, we'll just decode normally
        # In a real implementation, you might want to recreate CustomId objects
        return super().decode(value)


@pytest.mark.asyncio
async def test_custom_orjson_coder():
    """Test that custom OrjsonCoder can handle non-JSON serializable types."""
    pytest.importorskip("orjson")

    # Test with a CustomId object
    custom_id = CustomId("abc123")
    encoded = CustomOrjsonCoder.encode(custom_id)
    decoded = CustomOrjsonCoder.decode(encoded)
    assert decoded == "abc123"  # It's decoded as string

    # Test with nested structure containing CustomId
    data = {
        "id": CustomId("xyz789"),
        "items": [CustomId("item1"), CustomId("item2")],
        "metadata": {"owner_id": CustomId("owner123"), "name": "Test"},
    }

    encoded = CustomOrjsonCoder.encode(data)
    decoded = CustomOrjsonCoder.decode(encoded)

    assert decoded == {
        "id": "xyz789",
        "items": ["item1", "item2"],
        "metadata": {"owner_id": "owner123", "name": "Test"},
    }

    # Test None handling still works
    encoded = CustomOrjsonCoder.encode(None)
    decoded = CustomOrjsonCoder.decode(encoded)
    assert decoded is None


@pytest.mark.asyncio
async def test_custom_coder_with_cache_decorator():
    """Test that custom coder works with the cache decorator."""
    pytest.importorskip("orjson")

    from pydantic_cache import PydanticCache, cache
    from pydantic_cache.backends.inmemory import InMemoryBackend

    backend = InMemoryBackend()
    PydanticCache.init(backend=backend)

    @cache(expire=60, coder=CustomOrjsonCoder)
    async def get_custom_object(obj_id: str) -> dict:
        return {"id": CustomId(obj_id), "name": f"Object {obj_id}"}

    # First call - cache miss
    result1 = await get_custom_object("test123")
    assert result1 == {"id": CustomId("test123"), "name": "Object test123"}

    # Second call - cache hit (decoded as strings)
    result2 = await get_custom_object("test123")
    # After decoding from cache, CustomId becomes string
    assert result2 == {"id": "test123", "name": "Object test123"}
