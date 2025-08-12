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
        # Test string
        encoded = JsonCoder.encode("hello world")
        decoded = JsonCoder.decode(encoded)
        assert decoded == "hello world"

        # Test int
        encoded = JsonCoder.encode(42)
        decoded = JsonCoder.decode(encoded)
        assert decoded == 42

        # Test float
        encoded = JsonCoder.encode(3.14)
        decoded = JsonCoder.decode(encoded)
        assert decoded == 3.14

        # Test bool
        encoded = JsonCoder.encode(True)
        decoded = JsonCoder.decode(encoded)
        assert decoded is True

        # Test None
        encoded = JsonCoder.encode(None)
        decoded = JsonCoder.decode(encoded)
        assert decoded is None

    def test_encode_decode_collections(self):
        # Test list
        data = [1, 2, 3, "hello", {"key": "value"}]
        encoded = JsonCoder.encode(data)
        decoded = JsonCoder.decode(encoded)
        assert decoded == data

        # Test dict
        data = {"name": "test", "values": [1, 2, 3], "nested": {"a": 1}}
        encoded = JsonCoder.encode(data)
        decoded = JsonCoder.decode(encoded)
        assert decoded == data

    def test_encode_decode_datetime(self):
        dt = datetime.datetime(2024, 1, 1, 12, 0, 0)
        encoded = JsonCoder.encode(dt)
        decoded = JsonCoder.decode(encoded)
        assert decoded.year == 2024
        assert decoded.month == 1
        assert decoded.day == 1
        assert decoded.hour == 12

    def test_encode_decode_date(self):
        d = datetime.date(2024, 1, 1)
        encoded = JsonCoder.encode(d)
        decoded = JsonCoder.decode(encoded)
        assert decoded.year == 2024
        assert decoded.month == 1
        assert decoded.day == 1

    def test_encode_decode_decimal(self):
        dec = Decimal("123.45")
        encoded = JsonCoder.encode(dec)
        decoded = JsonCoder.decode(encoded)
        assert decoded == dec
        assert isinstance(decoded, Decimal)

    def test_encode_decode_pydantic_model(self):
        model = SampleModel(id=1, name="Test", created_at=datetime.datetime(2024, 1, 1), price=Decimal("99.99"))

        encoded = JsonCoder.encode(model)
        decoded = JsonCoder.decode(encoded)

        # JsonCoder returns dict, not the model instance
        assert decoded["id"] == 1
        assert decoded["name"] == "Test"
        # Price should be a Decimal object after decoding
        assert decoded["price"] == Decimal("99.99")

    def test_decode_as_type_pydantic(self):
        model = SampleModel(id=1, name="Test", created_at=datetime.datetime(2024, 1, 1), price=Decimal("99.99"))

        encoded = JsonCoder.encode(model)
        decoded = JsonCoder.decode_as_type(encoded, type_=SampleModel)

        # With type hint, should attempt to parse as Pydantic model
        assert isinstance(decoded, (dict, SampleModel))
        if isinstance(decoded, SampleModel):
            assert decoded.id == 1
            assert decoded.name == "Test"


class TestPickleCoder:
    def test_encode_decode_simple_types(self):
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
            encoded = PickleCoder.encode(value)
            decoded = PickleCoder.decode(encoded)
            assert decoded == value

    def test_encode_decode_datetime(self):
        dt = datetime.datetime(2024, 1, 1, 12, 0, 0)
        encoded = PickleCoder.encode(dt)
        decoded = PickleCoder.decode(encoded)
        assert decoded == dt
        assert isinstance(decoded, datetime.datetime)

    def test_encode_decode_pydantic_model(self):
        model = SampleModel(id=1, name="Test", created_at=datetime.datetime(2024, 1, 1), price=Decimal("99.99"))

        encoded = PickleCoder.encode(model)
        decoded = PickleCoder.decode(encoded)

        # Pickle preserves the exact type
        assert isinstance(decoded, SampleModel)
        assert decoded.id == 1
        assert decoded.name == "Test"
        assert decoded.created_at == datetime.datetime(2024, 1, 1)
        assert decoded.price == Decimal("99.99")

    def test_decode_as_type(self):
        # PickleCoder's decode_as_type ignores type hint
        model = SampleModel(id=1, name="Test")
        encoded = PickleCoder.encode(model)
        decoded = PickleCoder.decode_as_type(encoded, type_=dict)

        # Still returns SampleModel, not dict
        assert isinstance(decoded, SampleModel)

    def test_complex_nested_structure(self):
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

        encoded = PickleCoder.encode(data)
        decoded = PickleCoder.decode(encoded)

        assert len(decoded["models"]) == 2
        assert all(isinstance(m, SampleModel) for m in decoded["models"])
        assert decoded["models"][0].name == "First"
        assert decoded["metadata"]["version"] == 1.0
        assert decoded["metadata"]["tags"] == ["test", "pickle"]
