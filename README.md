# Pydantic Typed Cache

An async cache library for Pydantic models without FastAPI dependencies. This library provides a simple decorator-based caching mechanism for async functions that return Pydantic models or other Python objects.

> **Note**: This project was inspired by [fastapi-cache](https://github.com/long2ice/fastapi-cache) but designed to work independently of FastAPI/Starlette, making it suitable for any async Python application.

## Features

- 🚀 Simple decorator-based caching for async functions
- 🔄 Support for both async and sync functions (sync functions run in thread pool)
- 📦 Multiple backends: Redis, In-Memory
- 🎯 Type-safe with Pydantic model support
- 🔑 Customizable cache key generation
- 📝 Multiple serialization options (JSON, Pickle)
- ⚡ Zero FastAPI/Starlette dependencies
- 🔧 Flexible type conversion with `model` parameter
- ✅ Support for nullable/optional types with proper None handling
- 🎭 Support for Union types and complex type hints

## Installation

```bash
# Basic installation
pip install pydantic-typed-cache

# With orjson for faster JSON serialization
pip install pydantic-typed-cache[orjson]

# With development dependencies
pip install pydantic-typed-cache[dev]
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

## Advanced Features

### Type Conversion with `model` Parameter

The `model` parameter allows you to force type conversion of cached values. This works with any Python type, not just Pydantic models:

```python
# Convert string to int
@cache(model=int)
async def get_count() -> str:
    return "42"  # Will be converted to int 42

# Convert dict to Pydantic model
class UserResponse(BaseModel):
    id: int
    name: str

@cache(model=UserResponse)
async def get_user_data(user_id: int) -> dict:
    # Returns dict that will be converted to UserResponse
    return {"id": user_id, "name": "Alice"}

# Work with collections
@cache(model=list[int])
async def get_scores() -> list[str]:
    return ["95", "87", "92"]  # Converted to [95, 87, 92]

# Support Union types
@cache(model=int | str)
async def get_flexible_value(use_number: bool) -> any:
    return 123 if use_number else "hello"

# Support Optional types
@cache(model=int | None)
async def get_optional_value(value: str | None) -> str | None:
    return value  # "123" becomes 123, None stays None
```

### Nullable/Optional Type Support

The library properly handles None values in optional types, distinguishing between cached None values and cache misses:

```python
# Function returning Optional types
@cache(namespace="users")
async def get_user(user_id: int) -> User | None:
    if user_id < 0:
        return None  # This None will be cached
    return User(id=user_id, name="John", email="john@example.com")

# First call with -1
user = await get_user(-1)  # Returns None (cache miss, stores None)
user = await get_user(-1)  # Returns None (cache hit, retrieves None)

# Pydantic models with optional fields
class Profile(BaseModel):
    id: int
    bio: str | None = None
    age: int | None = None

@cache(namespace="profiles")
async def get_profile(user_id: int) -> Profile:
    return Profile(id=user_id, bio=None, age=None)  # None fields are properly cached
```

### Sync Function Support

Sync functions are automatically wrapped and run in a thread pool:

```python
@cache(namespace="compute")
def expensive_computation(x: int, y: int) -> int:
    # This sync function will be run in a thread pool
    import time
    time.sleep(1)
    return x * y

# Can be called as async
result = await expensive_computation(10, 20)
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

### Global Configuration

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

### Per-Decorator Configuration

```python
@cache(
    expire=120,           # Override default expiration
    namespace="users",    # Namespace for this function
    coder=PickleCoder,   # Override default coder
    key_builder=custom_key_builder,  # Custom key builder
    model=UserModel      # Force type conversion
)
async def cached_function():
    pass
```

## Serialization

### JsonCoder (Default)

- Human-readable cache values
- Good for debugging
- Supports most Python types and Pydantic models
- Moderate performance

### OrjsonCoder (Recommended for performance)

- **2-3x faster** than standard JSON
- Efficient datetime handling
- Better performance with large datasets
- Requires: `pip install pydantic-typed-cache[orjson]`

```python
from pydantic_cache import OrjsonCoder

PydanticCache.init(backend, coder=OrjsonCoder)
```

### PickleCoder

- Supports all Python objects
- Fast serialization
- Binary format (not human-readable)
- Better for complex nested structures

```python
from pydantic_cache.coder import JsonCoder, OrjsonCoder, PickleCoder

# Set globally with default instance
PydanticCache.init(backend, coder=OrjsonCoder())  # Recommended

# Or with custom configuration
custom_coder = OrjsonCoder(default=my_handler)
PydanticCache.init(backend, coder=custom_coder)

# Or per decorator
@cache(coder=JsonCoder())  # Default configuration
async def my_function():
    pass

# Or with custom configuration per function
@cache(coder=JsonCoder(default=my_handler))
async def my_other_function():
    pass
```

### Performance Comparison

| Coder | Speed | Human Readable | Size | Use Case |
|-------|-------|----------------|------|----------|
| JsonCoder | Moderate | ✅ | Small | Debugging, small data |
| OrjsonCoder | Fast | ✅ | Small | Production, large data |
| PickleCoder | Fast | ❌ | Medium | Complex objects |

### Custom Serialization

All coders now support instance-based configuration for custom serialization:

#### OrjsonCoder with Custom Types

```python
from pydantic_cache import OrjsonCoder

# Define handler for non-serializable types
def handle_objectid(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError  # Let orjson handle other types

# Create coder instance with custom handler
custom_coder = OrjsonCoder(default=handle_objectid)

# Use with decorator
@cache(coder=custom_coder)
async def get_document(doc_id: str) -> dict:
    return {
        "_id": ObjectId(doc_id),
        "name": "Document",
        "tags": [ObjectId("..."), ObjectId("...")]  # Nested structures handled automatically
    }
```

#### JsonCoder with Custom Handler

```python
from pydantic_cache import JsonCoder

def handle_custom_types(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, Decimal):
        return float(obj)  # Convert to float instead of string
    raise TypeError  # Let default encoder handle other types

# Create coder with custom handler (same interface as OrjsonCoder!)
custom_coder = JsonCoder(default=handle_custom_types)

@cache(coder=custom_coder)
async def get_data():
    return {"id": ObjectId("..."), "price": Decimal("99.99")}
```

#### PickleCoder with Protocol Version

```python
from pydantic_cache import PickleCoder
import pickle

# Use specific protocol version
coder = PickleCoder(protocol=pickle.HIGHEST_PROTOCOL)

@cache(coder=coder)
async def get_complex_object():
    return complex_python_object
```

## Cache Management

```python
# Clear specific key
await PydanticCache.clear(key="specific_key")

# Clear entire namespace
await PydanticCache.clear(namespace="users")

# Clear all cache
await PydanticCache.clear()

# Disable caching temporarily
PydanticCache.set_enable(False)

# Re-enable caching
PydanticCache.set_enable(True)

# Check if caching is enabled
is_enabled = PydanticCache.get_enable()
```

## Custom Key Builder

Create custom cache key generation logic:

```python
from pydantic_cache.types import KeyBuilder

def custom_key_builder(
    func,
    namespace: str,
    args: tuple,
    kwargs: dict
) -> str:
    # Custom logic to generate cache key
    func_name = func.__name__
    args_str = "_".join(str(arg) for arg in args)
    return f"{namespace}:{func_name}:{args_str}"

# Use globally
PydanticCache.init(backend, key_builder=custom_key_builder)

# Or per decorator
@cache(key_builder=custom_key_builder)
async def my_function():
    pass
```

## Examples

### Complex Type Conversions

```python
# Nested structures
@cache(model=list[list[int]])
async def get_matrix() -> list[list[str]]:
    return [["1", "2"], ["3", "4"]]  # Converted to [[1, 2], [3, 4]]

# List of Pydantic models
class Item(BaseModel):
    id: int
    name: str
    price: float

@cache(model=list[Item])
async def get_items() -> list[dict]:
    return [
        {"id": "1", "name": "Item 1", "price": "9.99"},
        {"id": "2", "name": "Item 2", "price": "19.99"}
    ]

# Complex Union types
@cache(model=User | dict | None)
async def get_flexible_data(data_type: str) -> any:
    if data_type == "user":
        return {"id": 1, "name": "Alice", "email": "alice@example.com"}
    elif data_type == "dict":
        return {"key": "value"}
    else:
        return None
```

### Model-to-Model Conversion

```python
class DetailedUser(BaseModel):
    id: int
    name: str
    email: str
    age: int
    bio: str

class SimpleUser(BaseModel):
    id: int
    name: str

# Convert DetailedUser to SimpleUser
@cache(model=SimpleUser)
async def get_simple_user(user_id: int) -> DetailedUser:
    return DetailedUser(
        id=user_id,
        name="Alice",
        email="alice@example.com",
        age=30,
        bio="Developer"
    )
    # Result will be SimpleUser with only id and name
```

### Working with External APIs

```python
class APIResponse(BaseModel):
    status: str
    data: dict
    timestamp: str | None = None

# Force API responses to be validated as Pydantic models
@cache(model=APIResponse, expire=300, namespace="api")
async def fetch_from_api(endpoint: str) -> dict:
    # Make actual API call here
    return {
        "status": "success",
        "data": {"result": "some data"},
        "timestamp": "2024-01-01T12:00:00Z"
    }

# Result is always validated as APIResponse model
response = await fetch_from_api("/users")
print(response.status)  # Type-safe access
```

## Testing

```python
import pytest
from pydantic_cache import PydanticCache
from pydantic_cache.backends.inmemory import InMemoryBackend

@pytest.fixture
async def cache_setup():
    backend = InMemoryBackend()
    PydanticCache.init(backend, prefix="test", expire=60)
    yield
    await backend.clear()

async def test_caching(cache_setup):
    call_count = 0
    
    @cache(namespace="test")
    async def get_value():
        nonlocal call_count
        call_count += 1
        return "result"
    
    result1 = await get_value()
    result2 = await get_value()
    
    assert result1 == result2
    assert call_count == 1  # Called only once due to caching
```

## Acknowledgments

This project was inspired by [fastapi-cache](https://github.com/long2ice/fastapi-cache) by @long2ice. While fastapi-cache provides excellent caching capabilities for FastAPI applications, pydantic-typed-cache was created to offer similar functionality for general async Python applications without the FastAPI/Starlette dependency.

## License

MIT