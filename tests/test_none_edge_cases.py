"""Test edge cases for None handling with the new "null" string encoding."""

import pytest

from pydantic_cache import cache
from pydantic_cache.coder import JsonCoder, OrjsonCoder


class TestNoneEdgeCases:
    @pytest.mark.asyncio
    async def test_none_vs_cache_miss_with_json_coder(self, cache_setup):
        """Test that None values are properly distinguished from cache misses with JsonCoder."""
        call_count = 0

        @cache(namespace="none_test", coder=JsonCoder())
        async def get_value(key: str) -> str | None:
            nonlocal call_count
            call_count += 1
            return None if key == "null" else key

        # First call returns None
        result = await get_value("null")
        assert result is None
        assert call_count == 1

        # Second call should get cached None
        result = await get_value("null")
        assert result is None
        assert call_count == 1  # No additional call - None was cached

        # Test with a different key to ensure proper caching behavior
        result = await get_value("test")
        assert result == "test"
        assert call_count == 2  # Function called for new key

    @pytest.mark.asyncio
    async def test_none_vs_cache_miss_with_orjson_coder(self, cache_setup):
        """Test that None values are properly distinguished from cache misses with OrjsonCoder."""
        pytest.importorskip("orjson")
        call_count = 0

        @cache(namespace="none_test_orjson", coder=OrjsonCoder())
        async def get_value(key: str) -> str | None:
            nonlocal call_count
            call_count += 1
            return None if key == "null" else key

        # First call returns None
        result = await get_value("null")
        assert result is None
        assert call_count == 1

        # Second call should get cached None
        result = await get_value("null")
        assert result is None
        assert call_count == 1  # No additional call - None was cached

    def test_none_encoding_decoding_json(self):
        """Test that None is properly encoded/decoded with JSON null."""
        coder = JsonCoder()

        # Test None encoding
        encoded = coder.encode(None)
        assert encoded == b"null"  # JSON null for None

        # Test None decoding
        decoded = coder.decode(b"null")
        assert decoded is None

        # Test that regular "null" string is different
        encoded_str = coder.encode("null")
        assert encoded_str == b'"null"'  # JSON string
        decoded_str = coder.decode(encoded_str)
        assert decoded_str == "null"

    def test_none_encoding_decoding_orjson(self):
        """Test that None is properly encoded/decoded with JSON null."""
        pytest.importorskip("orjson")
        coder = OrjsonCoder()

        # Test None encoding
        encoded = coder.encode(None)
        assert encoded == b"null"  # JSON null for None

        # Test None decoding
        decoded = coder.decode(b"null")
        assert decoded is None

        # Test that regular "null" string is different
        encoded_str = coder.encode("null")
        assert encoded_str == b'"null"'  # JSON string
        decoded_str = coder.decode(encoded_str)
        assert decoded_str == "null"

    def test_none_in_collections(self):
        """Test None values inside collections are handled correctly."""
        json_coder = JsonCoder()

        test_data = [
            {"key": None, "other": "value"},
            [None, 1, 2, None],
            (None, "test"),
        ]

        for data in test_data:
            # Test JsonCoder
            encoded = json_coder.encode(data)
            decoded = json_coder.decode(encoded)
            # Tuples become lists in JSON
            if isinstance(data, tuple):
                assert decoded == list(data)
            else:
                assert decoded == data

    def test_none_in_collections_orjson(self):
        """Test None values inside collections are handled correctly with OrjsonCoder."""
        pytest.importorskip("orjson")
        orjson_coder = OrjsonCoder()

        test_data = [
            {"key": None, "other": "value"},
            [None, 1, 2, None],
            (None, "test"),
        ]

        for data in test_data:
            encoded = orjson_coder.encode(data)
            decoded = orjson_coder.decode(encoded)
            # Tuples become lists in JSON
            if isinstance(data, tuple):
                assert decoded == list(data)
            else:
                assert decoded == data
