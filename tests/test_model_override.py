"""Tests for model override feature in cache decorator."""

import pytest
from pydantic import BaseModel, Field

from pydantic_cache import PydanticCache, cache
from pydantic_cache.backends.inmemory import InMemoryBackend


# Test models
class UserModel(BaseModel):
    id: int
    name: str
    email: str
    age: int | None = None


class SimpleUserModel(BaseModel):
    id: int
    name: str


class DetailedUserModel(BaseModel):
    id: int
    name: str
    email: str
    age: int | None = None
    bio: str = Field(default="No bio provided")
    is_active: bool = True


class ProductModel(BaseModel):
    id: int
    name: str
    price: float
    description: str | None = None


class TestModelOverride:
    @pytest.mark.asyncio
    async def test_dict_to_model_conversion(self, cache_setup):
        """Test that dict return values are converted to the specified model."""
        call_count = 0

        @cache(namespace="users", model=UserModel)
        async def get_user_dict(user_id: int) -> dict:
            nonlocal call_count
            call_count += 1
            return {
                "id": user_id,
                "name": f"User {user_id}",
                "email": f"user{user_id}@example.com",
                "age": 25,
            }

        # First call - should return UserModel instance
        user = await get_user_dict(1)
        assert isinstance(user, UserModel)
        assert user.id == 1
        assert user.name == "User 1"
        assert user.email == "user1@example.com"
        assert call_count == 1

        # Second call - should return cached UserModel
        user_cached = await get_user_dict(1)
        assert isinstance(user_cached, UserModel)
        assert user_cached.id == 1
        assert call_count == 1  # No additional call

    @pytest.mark.asyncio
    async def test_model_to_different_model_conversion(self, cache_setup):
        """Test converting one model to another model."""
        call_count = 0

        @cache(namespace="users", model=SimpleUserModel)
        async def get_detailed_user(user_id: int) -> DetailedUserModel:
            nonlocal call_count
            call_count += 1
            return DetailedUserModel(
                id=user_id,
                name=f"User {user_id}",
                email=f"user{user_id}@example.com",
                age=30,
                bio="Detailed bio",
                is_active=True,
            )

        # Should return SimpleUserModel with only id and name
        user = await get_detailed_user(1)
        assert isinstance(user, SimpleUserModel)
        assert user.id == 1
        assert user.name == "User 1"
        assert not hasattr(user, "email")  # SimpleUserModel doesn't have email
        assert call_count == 1

        # Cached version
        user_cached = await get_detailed_user(1)
        assert isinstance(user_cached, SimpleUserModel)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_nullable_with_model_override(self, cache_setup):
        """Test model override with nullable return values."""
        call_count = 0

        @cache(namespace="nullable", model=UserModel)
        async def maybe_get_user(user_id: int) -> dict | None:
            nonlocal call_count
            call_count += 1
            if user_id < 0:
                return None
            return {
                "id": user_id,
                "name": f"User {user_id}",
                "email": f"user{user_id}@example.com",
            }

        # Test None return
        result = await maybe_get_user(-1)
        assert result is None
        assert call_count == 1

        # Cached None
        result_cached = await maybe_get_user(-1)
        assert result_cached is None
        assert call_count == 1

        # Test dict to model conversion
        user = await maybe_get_user(1)
        assert isinstance(user, UserModel)
        assert user.id == 1
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_model_override_with_validation(self, cache_setup):
        """Test that model validation is applied when using model override."""

        @cache(namespace="products", model=ProductModel)
        async def get_product_dict(product_id: int) -> dict:
            return {
                "id": product_id,
                "name": f"Product {product_id}",
                "price": 99.99,
                # description is optional, not provided
            }

        product = await get_product_dict(1)
        assert isinstance(product, ProductModel)
        assert product.id == 1
        assert product.price == 99.99
        assert product.description is None  # Default value for optional field

    @pytest.mark.asyncio
    async def test_model_override_preserves_existing_model(self, cache_setup):
        """Test that if function already returns the specified model, it's preserved."""
        call_count = 0

        @cache(namespace="preserve", model=UserModel)
        async def get_user_model(user_id: int) -> UserModel:
            nonlocal call_count
            call_count += 1
            return UserModel(
                id=user_id,
                name=f"User {user_id}",
                email=f"user{user_id}@example.com",
            )

        # First call
        user = await get_user_model(1)
        assert isinstance(user, UserModel)
        assert user.id == 1
        assert call_count == 1

        # Cached call
        user_cached = await get_user_model(1)
        assert isinstance(user_cached, UserModel)
        assert user_cached.id == 1
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_model_override_with_different_coders(self):
        """Test model override works with both JSON and Pickle coders."""
        from pydantic_cache.coder import JsonCoder, PickleCoder

        for coder_class in [JsonCoder, PickleCoder]:
            backend = InMemoryBackend()
            PydanticCache.init(backend, coder=coder_class, prefix=coder_class.__name__)

            @cache(namespace="coders", model=UserModel)
            async def get_user_data() -> dict:
                return {"id": 1, "name": "Test User", "email": "test@example.com"}

            user = await get_user_data()
            assert isinstance(user, UserModel)
            assert user.name == "Test User"

            # Clear for next iteration
            await backend.clear()

    @pytest.mark.asyncio
    async def test_without_model_override(self, cache_setup):
        """Test that without model parameter, original behavior is preserved."""
        call_count = 0

        @cache(namespace="no_override")
        async def get_user_dict(user_id: int) -> dict:
            nonlocal call_count
            call_count += 1
            return {"id": user_id, "name": f"User {user_id}"}

        # Should return dict as originally defined
        result = await get_user_dict(1)
        assert isinstance(result, dict)
        assert result["id"] == 1
        assert call_count == 1

        # Cached version should also be dict
        result_cached = await get_user_dict(1)
        assert isinstance(result_cached, dict)
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_model_override_with_complex_types(self):
        """Test model override with lists and nested structures."""
        from pydantic_cache import PydanticCache
        from pydantic_cache.backends.inmemory import InMemoryBackend
        from pydantic_cache.coder import JsonCoder

        # Use JsonCoder to avoid pickle issues with local classes
        backend = InMemoryBackend()
        PydanticCache.init(backend, coder=JsonCoder, prefix="complex_test")

        class OrderItem(BaseModel):
            product_id: int
            quantity: int
            price: float

        class Order(BaseModel):
            id: int
            items: list[OrderItem]
            total: float

        @cache(namespace="orders", model=Order)
        async def get_order_dict(order_id: int) -> dict:
            return {
                "id": order_id,
                "items": [
                    {"product_id": 1, "quantity": 2, "price": 10.0},
                    {"product_id": 2, "quantity": 1, "price": 20.0},
                ],
                "total": 40.0,
            }

        order = await get_order_dict(100)
        assert isinstance(order, Order)
        assert order.id == 100
        assert len(order.items) == 2
        assert all(isinstance(item, OrderItem) for item in order.items)
        assert order.items[0].product_id == 1
        assert order.total == 40.0

    @pytest.mark.asyncio
    async def test_model_override_validation_error_handling(self, cache_setup):
        """Test that invalid data doesn't break caching when model validation fails."""
        call_count = 0

        @cache(namespace="invalid", model=UserModel)
        async def get_invalid_user_dict(user_id: int) -> dict:
            nonlocal call_count
            call_count += 1
            # Missing required 'name' field
            return {"id": user_id, "email": f"user{user_id}@example.com"}

        # Should still cache the original dict even if model validation fails
        result = await get_invalid_user_dict(1)
        # The result will be the original dict since validation failed
        assert isinstance(result, dict)
        assert result["id"] == 1
        assert call_count == 1

        # Cached version
        result_cached = await get_invalid_user_dict(1)
        assert isinstance(result_cached, dict)
        assert call_count == 1  # No additional call
