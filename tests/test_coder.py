import datetime
from decimal import Decimal

from pydantic import BaseModel

from pydantic_cache.coder import JsonCoder, PickleCoder


class SampleModel(BaseModel):
    id: int
    name: str
    created_at: datetime.datetime | None = None
    price: Decimal | None = None


class TestJsonCoder:
    def test_encode_decode_simple_types(self):
        coder = JsonCoder()
        # Test string
        encoded = coder.encode("hello world")
        decoded = coder.decode(encoded)
        assert decoded == "hello world"

        # Test int
        encoded = coder.encode(42)
        decoded = coder.decode(encoded)
        assert decoded == 42

        # Test float
        encoded = coder.encode(3.14)
        decoded = coder.decode(encoded)
        assert decoded == 3.14

        # Test bool
        encoded = coder.encode(True)
        decoded = coder.decode(encoded)
        assert decoded is True

        # Test None
        encoded = coder.encode(None)
        decoded = coder.decode(encoded)
        assert decoded is None

    def test_encode_decode_collections(self):
        coder = JsonCoder()
        # Test list
        data = [1, 2, 3, "hello", {"key": "value"}]
        encoded = coder.encode(data)
        decoded = coder.decode(encoded)
        assert decoded == data

        # Test dict
        data = {"name": "test", "values": [1, 2, 3], "nested": {"a": 1}}
        encoded = coder.encode(data)
        decoded = coder.decode(encoded)
        assert decoded == data

    def test_encode_decode_datetime(self):
        coder = JsonCoder()
        dt = datetime.datetime(2024, 1, 1, 12, 0, 0)
        encoded = coder.encode(dt)
        decoded = coder.decode(encoded)
        # Without type hints, datetime becomes ISO string
        assert isinstance(decoded, str)
        assert "2024-01-01" in decoded
        assert "12:00:00" in decoded

    def test_encode_decode_date(self):
        coder = JsonCoder()
        d = datetime.date(2024, 1, 1)
        encoded = coder.encode(d)
        decoded = coder.decode(encoded)
        # Without type hints, date becomes string
        assert isinstance(decoded, str)
        assert decoded == "2024-01-01"

    def test_encode_decode_decimal(self):
        coder = JsonCoder()
        dec = Decimal("123.45")
        encoded = coder.encode(dec)
        decoded = coder.decode(encoded)
        # Without type hints, Decimal becomes string
        assert decoded == "123.45"
        assert isinstance(decoded, str)

    def test_encode_decode_pydantic_model(self):
        coder = JsonCoder()
        model = SampleModel(id=1, name="Test", created_at=datetime.datetime(2024, 1, 1), price=Decimal("99.99"))

        encoded = coder.encode(model)
        decoded = coder.decode(encoded)

        # JsonCoder returns dict, not the model instance
        assert decoded["id"] == 1
        assert decoded["name"] == "Test"
        # Without type hints, datetime and Decimal become strings
        assert isinstance(decoded["created_at"], str)
        assert "2024-01-01" in decoded["created_at"]
        assert decoded["price"] == "99.99"

    def test_decode_as_type_pydantic(self):
        coder = JsonCoder()
        model = SampleModel(id=1, name="Test", created_at=datetime.datetime(2024, 1, 1), price=Decimal("99.99"))

        encoded = coder.encode(model)
        decoded = coder.decode_as_type(encoded, type_=SampleModel)

        # With type hint, should attempt to parse as Pydantic model
        assert isinstance(decoded, (dict, SampleModel))
        if isinstance(decoded, SampleModel):
            assert decoded.id == 1
            assert decoded.name == "Test"


class TestPickleCoder:
    def test_encode_decode_simple_types(self):
        coder = PickleCoder()
        # Test various types
        test_values = [
            "hello world",
            42,
            3.14,
            True,
            None,
            [1, 2, 3],
            {"key": "value"},
        ]

        for value in test_values:
            encoded = coder.encode(value)
            decoded = coder.decode(encoded)
            assert decoded == value

    def test_encode_decode_datetime(self):
        coder = PickleCoder()
        dt = datetime.datetime(2024, 1, 1, 12, 0, 0)
        encoded = coder.encode(dt)
        decoded = coder.decode(encoded)
        assert decoded == dt
        assert isinstance(decoded, datetime.datetime)

    def test_encode_decode_pydantic_model(self):
        coder = PickleCoder()
        model = SampleModel(id=1, name="Test", created_at=datetime.datetime(2024, 1, 1), price=Decimal("99.99"))

        encoded = coder.encode(model)
        decoded = coder.decode(encoded)

        # Pickle preserves the exact type
        assert isinstance(decoded, SampleModel)
        assert decoded.id == 1
        assert decoded.name == "Test"
        assert decoded.created_at == datetime.datetime(2024, 1, 1)
        assert decoded.price == Decimal("99.99")

    def test_decode_as_type(self):
        coder = PickleCoder()
        # PickleCoder's decode_as_type ignores type hint
        model = SampleModel(id=1, name="Test")
        encoded = coder.encode(model)
        decoded = coder.decode_as_type(encoded, type_=dict)

        # Still returns SampleModel, not dict
        assert isinstance(decoded, SampleModel)

    def test_complex_nested_structure(self):
        coder = PickleCoder()
        data = {
            "models": [
                SampleModel(id=1, name="First"),
                SampleModel(id=2, name="Second"),
            ],
            "metadata": {
                "created": datetime.datetime.now(),
                "version": 1.0,
                "tags": ["test", "pickle"],
            },
        }

        encoded = coder.encode(data)
        decoded = coder.decode(encoded)

        assert len(decoded["models"]) == 2
        assert all(isinstance(m, SampleModel) for m in decoded["models"])
        assert decoded["models"][0].name == "First"
        assert decoded["metadata"]["version"] == 1.0
        assert decoded["metadata"]["tags"] == ["test", "pickle"]
