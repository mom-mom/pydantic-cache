import asyncio
from typing import List, Optional

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
    age: Optional[int] = None


class Product(BaseModel):
    id: int
    name: str
    price: float
    description: Optional[str] = None


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
        return User(
            id=user_id,
            name=f"User {user_id}",
            email=f"user{user_id}@example.com",
            age=25
        )
    
    # Cache a function that returns a list
    @cache(namespace="products")
    async def get_products(category: str) -> List[Product]:
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
        return {
            "endpoint": endpoint,
            "params": params,
            "result": "some data",
            "timestamp": "2024-01-01T00:00:00"
        }
    
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


if __name__ == "__main__":
    print("=" * 50)
    print("In-Memory Backend Example")
    print("=" * 50)
    asyncio.run(example_inmemory())
    
    print("\n" + "=" * 50)
    print("Sync Function Example")
    print("=" * 50)
    asyncio.run(example_sync_function())
    
    # Uncomment to test Redis backend (requires Redis server)
    # print("\n" + "=" * 50)
    # print("Redis Backend Example")
    # print("=" * 50)
    # asyncio.run(example_redis())