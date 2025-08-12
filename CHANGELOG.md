# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2025-01-12

### Added
- Support for custom serialization in OrjsonCoder through `_serialize_value` method
- Documentation for extending coders to handle non-JSON serializable types

### Fixed
- OrjsonCoder now properly supports subclassing for custom type handling
- Improved extensibility for handling types like MongoDB ObjectId

## [1.0.0] - 2025-01-12

### Added
- Initial stable release of pydantic-typed-cache
- Core cache decorator with async/await support
- Multiple backend support (Redis, In-Memory)
- Multiple coder support (JsonCoder, PickleCoder, OrjsonCoder)
- Type conversion with `model` parameter supporting any Python type
- Support for nullable/optional types with proper None handling
- Support for Union types and complex type hints
- Sync function support via thread pool
- Custom key builder support
- Namespace-based cache organization
- Global enable/disable functionality
- Comprehensive test suite
- GitHub Actions CI/CD with OIDC-based PyPI publishing
- Optional orjson dependency for high-performance JSON serialization

### Features
- 🚀 Simple decorator-based caching for async functions
- 🔄 Support for both async and sync functions
- 📦 Multiple backends: Redis, In-Memory
- 🎯 Type-safe with Pydantic model support
- 🔑 Customizable cache key generation
- 📝 Multiple serialization options (JSON, Pickle, Orjson)
- ⚡ Zero FastAPI/Starlette dependencies
- 🔧 Flexible type conversion with TypeAdapter
- ✅ Support for nullable/optional types
- 🎭 Support for Union types and complex type hints

### Acknowledgments
This project was inspired by [fastapi-cache](https://github.com/long2ice/fastapi-cache) by @long2ice.

[1.0.0]: https://github.com/mom-mom/pydantic-cache/releases/tag/v1.0.0