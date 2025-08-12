import asyncio

from pydantic import BaseModel
from redis.asyncio import Redis

from pydantic_cache import PydanticCache, cache
from pydantic_cache.backends.inmemory import InMemoryBackend
from pydantic_cache.backends.redis import RedisBackend


# Define Pydantic models
class User(BaseModel):
    id: int
    name: str
    email: str
    age: int | None = None


class Product(BaseModel):
    id: int
    name: str
    price: float
    description: str | None = None


# Example with in-memory backend
async def example_inmemory():
    # Initialize cache with in-memory backend
    backend = InMemoryBackend()
    PydanticCache.init(backend, prefix="myapp", expire=30)

    # Cache a function that returns a Pydantic model
    @cache(expire=60, namespace="users")
    async def get_user(user_id: int) -> User:
        print(f"Fetching user {user_id} from database...")
        # Simulate database fetch
        await asyncio.sleep(1)
        return User(id=user_id, name=f"User {user_id}", email=f"user{user_id}@example.com", age=25)

    # Cache a function that returns a list
    @cache(namespace="products")
    async def get_products(category: str) -> list[Product]:
        print(f"Fetching products for category {category}...")
        # Simulate database fetch
        await asyncio.sleep(1)
        return [
            Product(id=1, name="Product 1", price=99.99),
            Product(id=2, name="Product 2", price=149.99),
        ]

    # Test caching
    print("First call (cache miss):")
    user = await get_user(1)
    print(f"Got user: {user}")

    print("\nSecond call (cache hit):")
    user = await get_user(1)
    print(f"Got user: {user}")

    print("\nFetching products (cache miss):")
    products = await get_products("electronics")
    print(f"Got {len(products)} products")

    print("\nFetching products again (cache hit):")
    products = await get_products("electronics")
    print(f"Got {len(products)} products")

    # Clear specific namespace
    cleared = await PydanticCache.clear(namespace="users")
    print(f"\nCleared {cleared} entries from 'users' namespace")

    print("\nFetching user after clear (cache miss):")
    user = await get_user(1)
    print(f"Got user: {user}")


# Example with Redis backend
async def example_redis():
    # Initialize Redis connection
    redis = Redis(host="localhost", port=6379, decode_responses=False)
    backend = RedisBackend(redis)
    PydanticCache.init(backend, prefix="myapp", expire=300)

    @cache(expire=120, namespace="api")
    async def fetch_data(endpoint: str, params: dict) -> dict:
        print(f"Fetching data from {endpoint} with params {params}")
        # Simulate API call
        await asyncio.sleep(2)
        return {"endpoint": endpoint, "params": params, "result": "some data", "timestamp": "2024-01-01T00:00:00"}

    # Test caching
    print("First API call (cache miss):")
    data = await fetch_data("users", {"page": 1})
    print(f"Got data: {data}")

    print("\nSecond API call (cache hit):")
    data = await fetch_data("users", {"page": 1})
    print(f"Got data: {data}")

    # Clean up
    await redis.close()


# Example showing sync function support
async def example_sync_function():
    backend = InMemoryBackend()
    PydanticCache.init(backend, prefix="sync", expire=60)

    @cache(namespace="compute")
    def compute_expensive(x: int, y: int) -> int:
        """Sync function that will be run in thread pool."""
        print(f"Computing {x} * {y}...")
        import time

        time.sleep(1)  # Simulate expensive computation
        return x * y

    # Even though compute_expensive is sync, the decorator makes it async
    result = await compute_expensive(10, 20)
    print(f"First call result: {result}")

    result = await compute_expensive(10, 20)  # This will be cached
    print(f"Second call result (cached): {result}")


# Example with model override
async def example_model_override():
    backend = InMemoryBackend()
    PydanticCache.init(backend, prefix="model_override", expire=60)

    # Define response models
    class UserResponse(BaseModel):
        id: int
        username: str
        email: str
        full_name: str | None = None

    class APIResponse(BaseModel):
        status: str
        data: dict
        timestamp: str | None = None

    # Force dict return to be converted to UserResponse
    @cache(namespace="users", model=UserResponse)
    async def get_user_from_api(user_id: int) -> dict:
        """Simulates getting raw dict from an API."""
        print(f"Fetching user {user_id} from API...")
        await asyncio.sleep(0.5)
        # Returns a raw dict
        return {
            "id": user_id,
            "username": f"user_{user_id}",
            "email": f"user{user_id}@api.example.com",
            "full_name": f"User Number {user_id}",
        }

    # Force any return to be converted to APIResponse
    @cache(namespace="api", model=APIResponse)
    async def fetch_api_data(endpoint: str) -> dict:
        """Simulates fetching data from an API endpoint."""
        print(f"Fetching data from {endpoint}...")
        await asyncio.sleep(0.5)
        return {
            "status": "success",
            "data": {"endpoint": endpoint, "result": "sample data"},
            "timestamp": "2024-01-01T12:00:00Z",
        }

    # Test model override with dict -> UserResponse
    print("First call (cache miss) - returns UserResponse:")
    user = await get_user_from_api(1)
    print(f"Type: {type(user).__name__}, Data: {user}")
    assert isinstance(user, UserResponse)

    print("\nSecond call (cache hit) - still UserResponse:")
    user_cached = await get_user_from_api(1)
    print(f"Type: {type(user_cached).__name__}, Data: {user_cached}")
    assert isinstance(user_cached, UserResponse)

    # Test with APIResponse
    print("\nAPI call (cache miss) - returns APIResponse:")
    api_data = await fetch_api_data("/users")
    print(f"Type: {type(api_data).__name__}, Status: {api_data.status}")
    assert isinstance(api_data, APIResponse)

    print("\nAPI call (cache hit) - still APIResponse:")
    api_data_cached = await fetch_api_data("/users")
    print(f"Type: {type(api_data_cached).__name__}, Status: {api_data_cached.status}")
    assert isinstance(api_data_cached, APIResponse)


async def example_type_conversion():
    """Example showing type conversion with primitive and complex types."""
    backend = InMemoryBackend()
    PydanticCache.init(backend, prefix="type_conversion", expire=60)

    # Convert string to int
    @cache(namespace="numbers", model=int)
    async def get_count_as_string() -> str:
        """Returns a string that will be converted to int."""
        print("Fetching count...")
        return "42"

    # Convert list of strings to list of ints
    @cache(namespace="lists", model=list[int])
    async def get_scores() -> list[str]:
        """Returns string scores that will be converted to ints."""
        print("Fetching scores...")
        return ["95", "87", "92", "100"]

    # Using Union types
    @cache(namespace="union", model=int | str)
    async def get_flexible_value(use_number: bool) -> any:
        """Returns either a number or string based on input."""
        print(f"Fetching flexible value (number={use_number})...")
        return 123 if use_number else "hello"

    # Using Optional types
    @cache(namespace="optional", model=int | None)
    async def get_optional_count(value: str | None) -> str | None:
        """Converts string to int or preserves None."""
        print(f"Processing optional value: {value}")
        return value

    # Test conversions
    print("--- Primitive Type Conversion ---")
    count = await get_count_as_string()
    print(f"String '42' converted to int: {count}, type: {type(count).__name__}")

    count_cached = await get_count_as_string()  # From cache
    print(f"Cached value: {count_cached}, type: {type(count_cached).__name__}")

    print("\n--- List Type Conversion ---")
    scores = await get_scores()
    print(f"String list converted to int list: {scores}")
    print(f"All integers: {all(isinstance(x, int) for x in scores)}")

    print("\n--- Union Type ---")
    num_value = await get_flexible_value(True)
    print(f"Number branch: {num_value}, type: {type(num_value).__name__}")

    str_value = await get_flexible_value(False)
    print(f"String branch: {str_value}, type: {type(str_value).__name__}")

    print("\n--- Optional Type ---")
    optional_none = await get_optional_count(None)
    print(f"None value: {optional_none}")

    optional_value = await get_optional_count("789")
    print(f"String '789' converted to Optional[int]: {optional_value}, type: {type(optional_value).__name__}")


if __name__ == "__main__":
    print("=" * 50)
    print("In-Memory Backend Example")
    print("=" * 50)
    asyncio.run(example_inmemory())

    print("\n" + "=" * 50)
    print("Sync Function Example")
    print("=" * 50)
    asyncio.run(example_sync_function())

    print("\n" + "=" * 50)
    print("Model Override Example")
    print("=" * 50)
    asyncio.run(example_model_override())

    print("\n" + "=" * 50)
    print("Type Conversion Example")
    print("=" * 50)
    asyncio.run(example_type_conversion())

    # Uncomment to test Redis backend (requires Redis server)
    # print("\n" + "=" * 50)
    # print("Redis Backend Example")
    # print("=" * 50)
    # asyncio.run(example_redis())
