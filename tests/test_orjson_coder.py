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
        coder = OrjsonCoder()
        # String
        encoded = coder.encode("hello")
        decoded = coder.decode(encoded)
        assert decoded == "hello"

        # Integer
        encoded = coder.encode(42)
        decoded = coder.decode(encoded)
        assert decoded == 42

        # Float
        encoded = coder.encode(3.14)
        decoded = coder.decode(encoded)
        assert decoded == 3.14

        # Boolean
        encoded = coder.encode(True)
        decoded = coder.decode(encoded)
        assert decoded is True

        # None
        encoded = coder.encode(None)
        decoded = coder.decode(encoded)
        assert decoded is None

    def test_encode_decode_collections(self):
        """Test encoding and decoding of collections."""
        coder = OrjsonCoder()
        # List
        data = [1, 2, 3, "hello", None]
        encoded = coder.encode(data)
        decoded = coder.decode(encoded)
        assert decoded == data

        # Dict
        data = {"key": "value", "number": 42, "nested": {"a": 1}}
        encoded = coder.encode(data)
        decoded = coder.decode(encoded)
        assert decoded == data

    def test_encode_decode_datetime(self):
        """Test encoding and decoding of datetime objects."""
        coder = OrjsonCoder()
        now = datetime.datetime.now()
        encoded = coder.encode(now)
        decoded = coder.decode(encoded)
        # Without type hints, datetime becomes ISO string
        assert isinstance(decoded, str)
        # Check that the string contains the date parts
        assert str(now.year) in decoded
        assert now.isoformat().startswith(decoded[:19])

    def test_encode_decode_pydantic_model(self):
        """Test encoding and decoding of Pydantic models."""
        coder = OrjsonCoder()
        model = SampleModel(id=1, name="Test", created_at=datetime.datetime(2024, 1, 1, 12, 0, 0))
        encoded = coder.encode(model)
        decoded = coder.decode(encoded)

        assert isinstance(decoded, dict)
        assert decoded["id"] == 1
        assert decoded["name"] == "Test"
        # Without type hints, datetime becomes ISO string
        assert isinstance(decoded["created_at"], str)
        assert "2024-01-01" in decoded["created_at"]

    def test_decode_as_type_pydantic(self):
        """Test decoding with type hint for Pydantic model."""
        coder = OrjsonCoder()
        model = SampleModel(id=1, name="Test")
        encoded = coder.encode(model)

        # Decode with type hint
        decoded = coder.decode_as_type(encoded, type_=SampleModel)
        assert isinstance(decoded, SampleModel)
        assert decoded.id == 1
        assert decoded.name == "Test"

    def test_performance_vs_json(self):
        """Test that OrjsonCoder works (performance test would need timing)."""
        coder = OrjsonCoder()
        # Create a large dataset
        data = [{"id": i, "name": f"Item {i}", "values": list(range(10))} for i in range(100)]

        # Test encoding and decoding
        encoded = coder.encode(data)
        decoded = coder.decode(encoded)

        assert len(decoded) == 100
        assert decoded[0]["id"] == 0
        assert decoded[-1]["id"] == 99

    def test_none_handling(self):
        """Test that None is properly handled to distinguish from cache miss."""
        coder = OrjsonCoder()
        # None should be encoded as JSON null
        encoded = coder.encode(None)
        decoded = coder.decode(encoded)
        assert decoded is None

        # The encoded value should be JSON null
        assert encoded == b"null"

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
            coder = OrjsonCoder()
            coder.encode("test")

        assert "pip install pydantic-typed-cache[orjson]" in str(exc_info.value)
