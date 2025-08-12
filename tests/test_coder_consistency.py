"""Test that JsonCoder and OrjsonCoder behave consistently."""

import datetime
from decimal import Decimal

import pytest
from pydantic import BaseModel

from pydantic_cache import JsonCoder, OrjsonCoder, PydanticJsonEncoder


class TestModel(BaseModel):
    """Test model with various field types."""

    id: int
    name: str
    created_at: datetime.datetime | None = None
    price: Decimal | None = None


class TestCoderConsistency:
    """Test that JsonCoder and OrjsonCoder produce consistent results."""

    @pytest.fixture
    def test_data(self):
        """Generate test data with various types."""
        return {
            "none": None,
            "string": "hello",
            "int": 42,
            "float": 3.14,
            "bool": True,
            "datetime": datetime.datetime(2024, 1, 1, 12, 0, 0),
            "date": datetime.date(2024, 1, 1),
            "decimal": Decimal("99.99"),
            "model": TestModel(id=1, name="Test", created_at=datetime.datetime(2024, 1, 1), price=Decimal("123.45")),
            "list": [1, 2, 3],
            "dict": {"nested": {"key": "value"}},
        }

    def test_basic_encoding_consistency(self, test_data):
        """Test that both coders handle basic types the same way."""
        pytest.importorskip("orjson")

        json_coder = JsonCoder()
        orjson_coder = OrjsonCoder()

        for key, value in test_data.items():
            # Encode with both
            json_encoded = json_coder.encode(value)
            orjson_encoded = orjson_coder.encode(value)

            # Decode with both
            json_decoded = json_coder.decode(json_encoded)
            orjson_decoded = orjson_coder.decode(orjson_encoded)

            # Both should produce the same result
            if key == "model":
                # Models become dicts after decoding
                assert isinstance(json_decoded, dict)
                assert isinstance(orjson_decoded, dict)
                assert json_decoded["id"] == orjson_decoded["id"]
                assert json_decoded["name"] == orjson_decoded["name"]
            elif key in ["datetime", "date", "decimal"]:
                # Without type hints, these become strings
                assert isinstance(json_decoded, str)
                assert isinstance(orjson_decoded, str)
                # Values should be similar (though format might differ slightly)
                if key == "decimal":
                    assert json_decoded == orjson_decoded
                else:
                    # Date/datetime strings contain the date
                    assert "2024-01-01" in json_decoded
                    assert "2024-01-01" in orjson_decoded
            else:
                assert json_decoded == orjson_decoded

    def test_cross_coder_compatibility(self, test_data):
        """Test that data encoded with one coder can be decoded by the other."""
        pytest.importorskip("orjson")

        json_coder = JsonCoder()
        orjson_coder = OrjsonCoder()

        for key, value in test_data.items():
            # Encode with JsonCoder, decode with OrjsonCoder
            json_encoded = json_coder.encode(value)
            orjson_decoded = orjson_coder.decode(json_encoded)

            # Encode with OrjsonCoder, decode with JsonCoder
            orjson_encoded = orjson_coder.encode(value)
            json_decoded = json_coder.decode(orjson_encoded)

            # Re-decode with original coder for comparison
            json_original = json_coder.decode(json_encoded)
            orjson_original = orjson_coder.decode(orjson_encoded)

            # All should be equivalent
            if key == "model":
                assert isinstance(orjson_decoded, dict)
                assert isinstance(json_decoded, dict)
                assert orjson_decoded["id"] == json_original["id"]
                assert json_decoded["id"] == orjson_original["id"]
            elif key in ["datetime", "date", "decimal"]:
                # All should be strings without type hints
                assert isinstance(orjson_decoded, str)
                assert isinstance(json_decoded, str)
                assert isinstance(json_original, str)
                assert isinstance(orjson_original, str)
            else:
                assert orjson_decoded == json_original
                assert json_decoded == orjson_original

    def test_custom_handlers_consistency(self):
        """Test that custom handlers work the same way in both coders."""
        pytest.importorskip("orjson")

        class CustomType:
            def __init__(self, value):
                self.value = value

        class CustomEncoder(PydanticJsonEncoder):
            def default(self, obj):
                if isinstance(obj, CustomType):
                    return {"custom": obj.value}
                return super().default(obj)

        json_coder = JsonCoder(encoder_class=CustomEncoder)
        orjson_coder = OrjsonCoder(encoder_class=CustomEncoder)

        # Test encoding and decoding
        custom_obj = CustomType("test_value")

        json_encoded = json_coder.encode(custom_obj)
        orjson_encoded = orjson_coder.encode(custom_obj)

        json_decoded = json_coder.decode(json_encoded)
        orjson_decoded = orjson_coder.decode(orjson_encoded)

        # Without object_hook, both return dicts
        assert isinstance(json_decoded, dict)
        assert isinstance(orjson_decoded, dict)
        assert json_decoded["custom"] == "test_value"
        assert orjson_decoded["custom"] == "test_value"

    def test_nested_special_types(self):
        """Test that nested special types are handled consistently."""
        pytest.importorskip("orjson")

        json_coder = JsonCoder()
        orjson_coder = OrjsonCoder()

        nested_data = {
            "dates": [datetime.date(2024, 1, 1), datetime.date(2024, 1, 2)],
            "decimals": {"price1": Decimal("10.50"), "price2": Decimal("20.75")},
            "mixed": {
                "datetime": datetime.datetime(2024, 1, 1, 12, 0, 0),
                "model": TestModel(id=1, name="Test", price=Decimal("99.99")),
            },
        }

        json_encoded = json_coder.encode(nested_data)
        orjson_encoded = orjson_coder.encode(nested_data)

        json_decoded = json_coder.decode(json_encoded)
        orjson_decoded = orjson_coder.decode(orjson_encoded)

        # Without type hints, dates become strings
        assert all(isinstance(d, str) for d in json_decoded["dates"])
        assert all(isinstance(d, str) for d in orjson_decoded["dates"])
        assert json_decoded["dates"][0] == "2024-01-01"

        # Without type hints, decimals become strings
        assert isinstance(json_decoded["decimals"]["price1"], str)
        assert isinstance(orjson_decoded["decimals"]["price1"], str)
        assert json_decoded["decimals"]["price1"] == "10.50"

        # Without type hints, datetime becomes string
        assert isinstance(json_decoded["mixed"]["datetime"], str)
        assert isinstance(orjson_decoded["mixed"]["datetime"], str)
        assert "2024-01-01" in json_decoded["mixed"]["datetime"]
