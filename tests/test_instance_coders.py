"""Tests for instance-based coder features."""

import json
from decimal import Decimal

import pytest
from pydantic import BaseModel

from pydantic_cache import JsonCoder, OrjsonCoder, PickleCoder
from pydantic_cache.coder import JsonEncoder


class CustomModel(BaseModel):
    """Test model for custom encoding."""

    id: str
    value: int


def custom_default(obj):
    """Custom default function that handles Decimal and CustomModel."""
    if isinstance(obj, Decimal):
        return float(obj)  # Convert to float instead of string
    if isinstance(obj, CustomModel):
        return {"custom_id": obj.id, "custom_value": obj.value}
    raise TypeError


class CustomJsonEncoderClass(JsonEncoder):
    """Custom encoder class that extends JsonEncoder."""

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)  # Convert to float instead of string
        if isinstance(obj, CustomModel):
            return {"custom_id": obj.id, "custom_value": obj.value}
        # Fall back to parent class
        return super().default(obj)


def custom_object_hook(obj):
    """Custom object hook for decoding."""
    if "custom_id" in obj and "custom_value" in obj:
        return CustomModel(id=obj["custom_id"], value=obj["custom_value"])
    return obj


class TestInstanceBasedCoders:
    """Test suite for instance-based coder features."""

    def test_json_coder_with_custom_encoder_class(self):
        """Test JsonCoder with custom encoder class."""
        coder = JsonCoder(encoder_class=CustomJsonEncoderClass)

        # Test Decimal encoding
        dec = Decimal("123.45")
        encoded = coder.encode(dec)
        decoded = coder.decode(encoded)
        assert decoded == 123.45  # Float instead of Decimal

        # Test custom model encoding
        model = CustomModel(id="test", value=42)
        encoded = coder.encode(model)
        decoded_data = json.loads(encoded)
        assert decoded_data == {"custom_id": "test", "custom_value": 42}

    def test_json_coder_with_custom_encoder_dict_output(self):
        """Test JsonCoder with custom encoder that outputs dict."""
        coder = JsonCoder(encoder_class=CustomJsonEncoderClass)

        model = CustomModel(id="test", value=42)
        encoded = coder.encode(model)
        decoded = coder.decode(encoded)

        # Without object_hook, should decode to dict with custom fields
        assert isinstance(decoded, dict)
        assert decoded["custom_id"] == "test"
        assert decoded["custom_value"] == 42

    def test_orjson_coder_with_custom_encoder(self):
        """Test OrjsonCoder with custom encoder class."""
        pytest.importorskip("orjson")

        class CustomType:
            def __init__(self, name: str):
                self.name = name

        class CustomOrjsonEncoder(JsonEncoder):
            def default(self, obj):
                if isinstance(obj, CustomType):
                    return {"type": "custom", "name": obj.name}
                return super().default(obj)

        coder = OrjsonCoder(encoder_class=CustomOrjsonEncoder)

        # Test custom type encoding
        custom = CustomType("test")
        encoded = coder.encode(custom)
        decoded = coder.decode(encoded)
        assert decoded == {"type": "custom", "name": "test"}

        # Test nested custom types
        data = {"items": [CustomType("a"), CustomType("b")], "single": CustomType("c")}
        encoded = coder.encode(data)
        decoded = coder.decode(encoded)
        assert decoded == {
            "items": [{"type": "custom", "name": "a"}, {"type": "custom", "name": "b"}],
            "single": {"type": "custom", "name": "c"},
        }

    def test_pickle_coder_with_protocol(self):
        """Test PickleCoder with custom protocol."""
        import pickle

        # Test with different protocols
        for protocol in [pickle.HIGHEST_PROTOCOL, 4, 3]:
            coder = PickleCoder(protocol=protocol)

            data = {"test": "data", "number": 42}
            encoded = coder.encode(data)
            decoded = coder.decode(encoded)
            assert decoded == data

    def test_coder_instances_are_independent(self):
        """Test that different coder instances are independent."""
        coder1 = JsonCoder()
        coder2 = JsonCoder(encoder_class=CustomJsonEncoderClass)

        dec = Decimal("99.99")

        # coder1 should encode Decimal as string (default)
        encoded1 = coder1.encode(dec)
        decoded1 = coder1.decode(encoded1)
        assert isinstance(decoded1, str)
        assert decoded1 == "99.99"

        # coder2 should encode Decimal as float (custom)
        encoded2 = coder2.encode(dec)
        decoded2 = coder2.decode(encoded2)
        assert isinstance(decoded2, float)
        assert decoded2 == 99.99

    @pytest.mark.asyncio
    async def test_instance_coders_with_cache_decorator(self):
        """Test using instance coders with cache decorator."""
        from pydantic_cache import PydanticCache, cache
        from pydantic_cache.backends.inmemory import InMemoryBackend

        backend = InMemoryBackend()
        PydanticCache.init(backend=backend)

        call_count = 0

        # Use custom JsonCoder instance with encoder class
        custom_coder = JsonCoder(encoder_class=CustomJsonEncoderClass)

        @cache(coder=custom_coder)
        async def get_decimal_value() -> Decimal:
            nonlocal call_count
            call_count += 1
            return Decimal("99.99")

        # First call - cache miss
        result1 = await get_decimal_value()
        assert result1 == Decimal("99.99")
        assert call_count == 1

        # Second call - cache hit (but decoded as float due to custom encoder)
        result2 = await get_decimal_value()
        assert result2 == 99.99  # Float, not Decimal
        assert call_count == 1  # Still 1, used cache

    def test_orjson_coder_handles_nested_automatically(self):
        """Test that OrjsonCoder handles nested structures automatically."""
        pytest.importorskip("orjson")

        class SpecialValue:
            def __init__(self, val):
                self.val = val

        class SpecialEncoder(JsonEncoder):
            def default(self, obj):
                if isinstance(obj, SpecialValue):
                    return f"special:{obj.val}"
                return super().default(obj)

        coder = OrjsonCoder(encoder_class=SpecialEncoder)

        # Deep nested structure
        data = {
            "level1": {
                "level2": {
                    "level3": [SpecialValue("a"), SpecialValue("b")],
                    "normal": "value",
                },
                "items": [{"special": SpecialValue("c")}, {"regular": 123}],
            }
        }

        encoded = coder.encode(data)
        decoded = coder.decode(encoded)

        assert decoded == {
            "level1": {
                "level2": {"level3": ["special:a", "special:b"], "normal": "value"},
                "items": [{"special": "special:c"}, {"regular": 123}],
            }
        }
