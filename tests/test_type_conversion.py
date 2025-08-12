"""Tests for type conversion feature with primitive and complex types."""

import pytest
from pydantic import BaseModel

from pydantic_cache import PydanticCache, cache
from pydantic_cache.backends.inmemory import InMemoryBackend


class TestPrimitiveTypeConversion:
    """Test conversion to primitive types."""

    @pytest.mark.asyncio
    async def test_string_to_int_conversion(self, cache_setup):
        """Test converting string return values to int."""
        call_count = 0

        @cache(namespace="numbers", model=int)
        async def get_number_as_string(value: int) -> str:
            nonlocal call_count
            call_count += 1
            return str(value * 2)

        # First call - should convert "20" to 20
        result = await get_number_as_string(10)
        assert result == 20
        assert isinstance(result, int)
        assert call_count == 1

        # Cached call
        result_cached = await get_number_as_string(10)
        assert result_cached == 20
        assert isinstance(result_cached, int)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_number_to_float_conversion(self, cache_setup):
        """Test converting int/string to float."""
        call_count = 0

        @cache(namespace="floats", model=float)
        async def get_value() -> str:
            nonlocal call_count
            call_count += 1
            return "3.14159"

        result = await get_value()
        assert result == 3.14159
        assert isinstance(result, float)
        assert call_count == 1

        # Cached
        result_cached = await get_value()
        assert result_cached == 3.14159
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_to_bool_conversion(self, cache_setup):
        """Test converting various values to bool."""
        call_count = 0

        @cache(namespace="bools", model=bool)
        async def get_bool_value(value: str) -> str:
            nonlocal call_count
            call_count += 1
            return value

        # "true" -> True
        result = await get_bool_value("true")
        assert result is True
        assert isinstance(result, bool)
        assert call_count == 1

        # "false" -> False
        result = await get_bool_value("false")
        assert result is False
        assert isinstance(result, bool)
        assert call_count == 2

        # Cached
        result_cached = await get_bool_value("true")
        assert result_cached is True
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_to_str_conversion(self, cache_setup):
        """Test string type validation."""
        call_count = 0

        @cache(namespace="strings", model=str)
        async def get_string_value(value: str) -> str:
            nonlocal call_count
            call_count += 1
            # Return a string value
            return f"Value: {value}"

        result = await get_string_value("test")
        assert result == "Value: test"
        assert isinstance(result, str)
        assert call_count == 1

        # Cached
        result_cached = await get_string_value("test")
        assert result_cached == "Value: test"
        assert call_count == 1


class TestCollectionTypeConversion:
    """Test conversion to collection types."""

    @pytest.mark.asyncio
    async def test_list_int_conversion(self, cache_setup):
        """Test converting list of strings to list of ints."""
        call_count = 0

        @cache(namespace="lists", model=list[int])
        async def get_number_list() -> list[str]:
            nonlocal call_count
            call_count += 1
            return ["1", "2", "3", "4", "5"]

        result = await get_number_list()
        assert result == [1, 2, 3, 4, 5]
        assert all(isinstance(x, int) for x in result)
        assert call_count == 1

        # Cached
        result_cached = await get_number_list()
        assert result_cached == [1, 2, 3, 4, 5]
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_dict_conversion(self, cache_setup):
        """Test converting to dict with type validation."""
        call_count = 0

        @cache(namespace="dicts", model=dict[str, int])
        async def get_scores() -> dict:
            nonlocal call_count
            call_count += 1
            return {"alice": "100", "bob": "95", "charlie": "88"}

        result = await get_scores()
        assert result == {"alice": 100, "bob": 95, "charlie": 88}
        assert all(isinstance(v, int) for v in result.values())
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_tuple_conversion(self, cache_setup):
        """Test converting to tuple."""
        call_count = 0

        @cache(namespace="tuples", model=tuple[int, str, float])
        async def get_mixed_tuple() -> list:
            nonlocal call_count
            call_count += 1
            return ["42", "hello", "3.14"]

        result = await get_mixed_tuple()
        assert result == (42, "hello", 3.14)
        assert isinstance(result, tuple)
        assert isinstance(result[0], int)
        assert isinstance(result[1], str)
        assert isinstance(result[2], float)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_set_conversion(self, cache_setup):
        """Test converting to set."""
        call_count = 0

        @cache(namespace="sets", model=set[int])
        async def get_unique_numbers() -> list[str]:
            nonlocal call_count
            call_count += 1
            return ["1", "2", "2", "3", "3", "3"]

        result = await get_unique_numbers()
        assert result == {1, 2, 3}
        assert isinstance(result, set)
        assert all(isinstance(x, int) for x in result)
        assert call_count == 1


class TestUnionOptionalConversion:
    """Test conversion with Union and Optional types."""

    @pytest.mark.asyncio
    async def test_union_type_conversion(self, cache_setup):
        """Test Union type conversions."""
        call_count = 0

        @cache(namespace="union", model=int | str)
        async def get_union_value(use_int: bool) -> any:
            nonlocal call_count
            call_count += 1
            if use_int:
                return 123  # Already an int
            return "hello"  # Already a str

        # Test int branch
        result = await get_union_value(True)
        assert result == 123
        assert isinstance(result, int)
        assert call_count == 1

        # Test str branch
        result = await get_union_value(False)
        assert result == "hello"
        assert isinstance(result, str)
        assert call_count == 2

        # Test that strings that look like numbers stay as strings with Union[str, int]
        @cache(namespace="union2", model=str | int)
        async def get_string_number() -> str:
            return "123"

        # Union[str, int] will keep "123" as string since it's valid for str
        result = await get_string_number()
        assert result == "123"
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_optional_int_conversion(self, cache_setup):
        """Test Optional[int] conversions."""
        call_count = 0

        @cache(namespace="optional", model=int | None)
        async def get_optional_number(value: str | None) -> str | None:
            nonlocal call_count
            call_count += 1
            return value

        # Test None
        result = await get_optional_number(None)
        assert result is None
        assert call_count == 1

        # Test string to int
        result = await get_optional_number("456")
        assert result == 456
        assert isinstance(result, int)
        assert call_count == 2

        # Cached
        result_cached = await get_optional_number("456")
        assert result_cached == 456
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_union_with_basemodel(self):
        """Test Union including BaseModel."""
        from pydantic_cache.coder import JsonCoder

        # Use JsonCoder to avoid pickle issues with local classes
        backend = InMemoryBackend()
        PydanticCache.init(backend, coder=JsonCoder, prefix="test_union_model")

        class Person(BaseModel):
            name: str
            age: int

        call_count = 0

        @cache(namespace="union_model", model=Person | dict | None)
        async def get_data(data_type: str) -> any:
            nonlocal call_count
            call_count += 1
            if data_type == "person":
                return {"name": "Alice", "age": 30}
            elif data_type == "dict":
                return {"key": "value"}
            else:
                return None

        # Test Person conversion
        result = await get_data("person")
        assert isinstance(result, Person)
        assert result.name == "Alice"
        assert result.age == 30
        assert call_count == 1

        # Test dict (no conversion needed)
        result = await get_data("dict")
        assert isinstance(result, dict)
        assert result == {"key": "value"}
        assert call_count == 2

        # Test None
        result = await get_data("none")
        assert result is None
        assert call_count == 3


class TestComplexTypeConversion:
    """Test complex nested type conversions."""

    @pytest.mark.asyncio
    async def test_nested_list_conversion(self, cache_setup):
        """Test nested list type conversion."""
        call_count = 0

        @cache(namespace="nested", model=list[list[int]])
        async def get_matrix() -> list[list[str]]:
            nonlocal call_count
            call_count += 1
            return [["1", "2", "3"], ["4", "5", "6"], ["7", "8", "9"]]

        result = await get_matrix()
        expected = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        assert result == expected
        assert all(all(isinstance(x, int) for x in row) for row in result)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_list_of_models_conversion(self):
        """Test converting list of dicts to list of models."""
        from pydantic_cache.coder import JsonCoder

        # Use JsonCoder to avoid pickle issues with local classes
        backend = InMemoryBackend()
        PydanticCache.init(backend, coder=JsonCoder, prefix="test_items")

        class Item(BaseModel):
            id: int
            name: str
            price: float

        call_count = 0

        @cache(namespace="items", model=list[Item])
        async def get_items() -> list[dict]:
            nonlocal call_count
            call_count += 1
            return [
                {"id": "1", "name": "Item 1", "price": "9.99"},
                {"id": "2", "name": "Item 2", "price": "19.99"},
            ]

        result = await get_items()
        assert len(result) == 2
        assert all(isinstance(item, Item) for item in result)
        assert result[0].id == 1
        assert result[0].price == 9.99
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_conversion_failure_preserves_original(self, cache_setup):
        """Test that failed conversions preserve the original value."""
        call_count = 0

        @cache(namespace="failure", model=int)
        async def get_invalid_int() -> str:
            nonlocal call_count
            call_count += 1
            return "not_a_number"

        # Should return original value when conversion fails
        result = await get_invalid_int()
        assert result == "not_a_number"
        assert isinstance(result, str)
        assert call_count == 1

        # Cached version
        result_cached = await get_invalid_int()
        assert result_cached == "not_a_number"
        assert call_count == 1
