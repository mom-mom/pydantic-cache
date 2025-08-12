# Pydantic Cache

An async cache library for Pydantic models without FastAPI dependencies. This library provides a simple decorator-based caching mechanism for async functions that return Pydantic models or other Python objects.

## Features

- 🚀 Simple decorator-based caching for async functions
- 🔄 Support for both async and sync functions (sync functions run in thread pool)
- 📦 Multiple backends: Redis, In-Memory
- 🎯 Type-safe with Pydantic model support
- 🔑 Customizable cache key generation
- 📝 Multiple serialization options (JSON, Pickle)
- ⚡ Zero FastAPI/Starlette dependencies

## Installation

```bash
pip install pydantic-cache
```

## Quick Start

```python
import asyncio
from pydantic import BaseModel
from pydantic_cache import PydanticCache, cache
from pydantic_cache.backends.inmemory import InMemoryBackend

# Define a Pydantic model
class User(BaseModel):
    id: int
    name: str
    email: str

# Initialize cache
backend = InMemoryBackend()
PydanticCache.init(backend, prefix="myapp", expire=60)

# Cache a function
@cache(expire=120, namespace="users")
async def get_user(user_id: int) -> User:
    # Expensive operation (e.g., database query)
    return User(id=user_id, name="John", email="john@example.com")

# Use the cached function
async def main():
    user = await get_user(1)  # First call - cache miss
    user = await get_user(1)  # Second call - cache hit
    
asyncio.run(main())
```

## Backends

### In-Memory Backend

Perfect for development and testing:

```python
from pydantic_cache.backends.inmemory import InMemoryBackend

backend = InMemoryBackend()
PydanticCache.init(backend)
```

### Redis Backend

For production use with persistence:

```python
from redis.asyncio import Redis
from pydantic_cache.backends.redis import RedisBackend

redis = Redis(host="localhost", port=6379)
backend = RedisBackend(redis)
PydanticCache.init(backend)
```

## Configuration

```python
PydanticCache.init(
    backend=backend,
    prefix="myapp",        # Prefix for all cache keys
    expire=300,            # Default expiration in seconds
    coder=JsonCoder,       # Serialization method (JsonCoder or PickleCoder)
    key_builder=my_key_builder,  # Custom key builder function
    enable=True            # Enable/disable caching globally
)
```

## Cache Management

```python
# Clear specific key
await PydanticCache.clear(key="specific_key")

# Clear entire namespace
await PydanticCache.clear(namespace="users")

# Disable caching temporarily
PydanticCache.set_enable(False)
```

## License

MIT