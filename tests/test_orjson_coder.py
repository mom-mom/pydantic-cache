"""Tests for OrjsonCoder."""

import datetime

import pytest
from pydantic import BaseModel

from pydantic_cache.coder import OrjsonCoder

# Skip all tests if orjson is not installed
pytest.importorskip("orjson")


class SampleModel(BaseModel):
    id: int
    name: str
    created_at: datetime.datetime | None = None


class TestOrjsonCoder:
    def test_encode_decode_simple_types(self):
        """Test encoding and decoding of simple types."""
        # String
        encoded = OrjsonCoder.encode("hello")
        decoded = OrjsonCoder.decode(encoded)
        assert decoded == "hello"

        # Integer
        encoded = OrjsonCoder.encode(42)
        decoded = OrjsonCoder.decode(encoded)
        assert decoded == 42

        # Float
        encoded = OrjsonCoder.encode(3.14)
        decoded = OrjsonCoder.decode(encoded)
        assert decoded == 3.14

        # Boolean
        encoded = OrjsonCoder.encode(True)
        decoded = OrjsonCoder.decode(encoded)
        assert decoded is True

        # None
        encoded = OrjsonCoder.encode(None)
        decoded = OrjsonCoder.decode(encoded)
        assert decoded is None

    def test_encode_decode_collections(self):
        """Test encoding and decoding of collections."""
        # List
        data = [1, 2, 3, "hello", None]
        encoded = OrjsonCoder.encode(data)
        decoded = OrjsonCoder.decode(encoded)
        assert decoded == data

        # Dict
        data = {"key": "value", "number": 42, "nested": {"a": 1}}
        encoded = OrjsonCoder.encode(data)
        decoded = OrjsonCoder.decode(encoded)
        assert decoded == data

    def test_encode_decode_datetime(self):
        """Test encoding and decoding of datetime objects."""
        # orjson automatically handles datetime
        now = datetime.datetime.now()
        encoded = OrjsonCoder.encode(now)
        decoded = OrjsonCoder.decode(encoded)
        # orjson returns datetime as ISO format string
        assert isinstance(decoded, str)
        assert now.isoformat().startswith(decoded[:19])

    def test_encode_decode_pydantic_model(self):
        """Test encoding and decoding of Pydantic models."""
        model = SampleModel(id=1, name="Test", created_at=datetime.datetime(2024, 1, 1, 12, 0, 0))
        encoded = OrjsonCoder.encode(model)
        decoded = OrjsonCoder.decode(encoded)

        assert isinstance(decoded, dict)
        assert decoded["id"] == 1
        assert decoded["name"] == "Test"
        # datetime is serialized as string
        assert "2024-01-01" in decoded["created_at"]

    def test_decode_as_type_pydantic(self):
        """Test decoding with type hint for Pydantic model."""
        model = SampleModel(id=1, name="Test")
        encoded = OrjsonCoder.encode(model)

        # Decode with type hint
        decoded = OrjsonCoder.decode_as_type(encoded, type_=SampleModel)
        assert isinstance(decoded, SampleModel)
        assert decoded.id == 1
        assert decoded.name == "Test"

    def test_performance_vs_json(self):
        """Test that OrjsonCoder works (performance test would need timing)."""
        # Create a large dataset
        data = [{"id": i, "name": f"Item {i}", "values": list(range(10))} for i in range(100)]

        # Test encoding and decoding
        encoded = OrjsonCoder.encode(data)
        decoded = OrjsonCoder.decode(encoded)

        assert len(decoded) == 100
        assert decoded[0]["id"] == 0
        assert decoded[-1]["id"] == 99

    def test_none_handling(self):
        """Test that None is properly handled to distinguish from cache miss."""
        # None should be encoded with special marker
        encoded = OrjsonCoder.encode(None)
        decoded = OrjsonCoder.decode(encoded)
        assert decoded is None

        # The encoded value should contain our special marker
        import orjson

        raw = orjson.loads(encoded)
        assert raw == {"_spec_type": "none"}

    def test_import_error_without_orjson(self, monkeypatch):
        """Test that proper error is raised when orjson is not installed."""
        # Temporarily remove orjson from sys.modules
        import sys

        original_modules = sys.modules.copy()

        # Remove orjson if it exists
        sys.modules.pop("orjson", None)

        # Mock import to raise ImportError
        def mock_import(name, *args):
            if name == "orjson":
                raise ImportError("No module named 'orjson'")
            return original_modules.get(name)

        monkeypatch.setattr("builtins.__import__", mock_import)

        with pytest.raises(ImportError) as exc_info:
            OrjsonCoder.encode("test")

        assert "pip install pydantic-typed-cache[orjson]" in str(exc_info.value)
