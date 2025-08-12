import datetime
import json
import pickle  # nosec:B403
import types
from collections.abc import Callable
from decimal import Decimal
from typing import (
    Any,
    TypeVar,
    Union,
    get_args,
    get_origin,
    overload,
)

import pendulum
from pydantic import BaseModel
from pydantic_core import to_jsonable_python

_T = TypeVar("_T", bound=type)

CONVERTERS: dict[str, Callable[[str], Any]] = {
    "date": lambda x: pendulum.parse(x, exact=True),
    "datetime": lambda x: pendulum.parse(x, exact=True),
    "decimal": Decimal,
}


class JsonEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if o is None:
            # Explicitly mark None values
            return {"_spec_type": "none"}
        elif isinstance(o, datetime.datetime):
            return {"val": str(o), "_spec_type": "datetime"}
        elif isinstance(o, datetime.date):
            return {"val": str(o), "_spec_type": "date"}
        elif isinstance(o, Decimal):
            return {"val": str(o), "_spec_type": "decimal"}
        elif isinstance(o, BaseModel):
            return o.model_dump()
        else:
            try:
                return to_jsonable_python(o)
            except TypeError:
                return super().default(o)


def object_hook(obj: Any) -> Any:
    _spec_type = obj.get("_spec_type")
    if not _spec_type:
        return obj

    if _spec_type == "none":
        return None
    elif _spec_type in CONVERTERS:
        return CONVERTERS[_spec_type](obj["val"])
    else:
        raise TypeError(f"Unknown {_spec_type}")


class Coder:
    """Base class for encoding/decoding cache values.

    Can be used both as class methods (for backward compatibility) or as instances.
    """

    def encode(self, value: Any) -> bytes:
        """Encode a value to bytes for storage."""
        raise NotImplementedError

    def decode(self, value: bytes) -> Any:
        """Decode bytes from storage to a value."""
        raise NotImplementedError

    @overload
    def decode_as_type(self, value: bytes, *, type_: _T) -> _T: ...

    @overload
    def decode_as_type(self, value: bytes, *, type_: None) -> Any: ...

    def decode_as_type(self, value: bytes, *, type_: _T | None) -> _T | Any:
        """Decode value to the specific given type

        The default implementation tries to convert the value using Pydantic if it's a BaseModel.
        """
        result = self.decode(value)

        if type_ is not None:
            # Handle Optional types (Union[X, None] or X | None)
            origin = get_origin(type_)
            # Check for both typing.Union and types.UnionType (Python 3.10+ with | operator)
            if origin is Union or origin is types.UnionType:
                # Get the non-None type from Optional
                args = get_args(type_)
                # Filter out NoneType
                non_none_types = [t for t in args if t is not type(None)]
                if len(non_none_types) == 1:
                    # This is Optional[T], extract T
                    actual_type = non_none_types[0]
                    # If result is None, return it as is
                    if result is None:
                        return result
                    # Otherwise try to convert to the actual type
                    type_ = actual_type

            # If type_ is a Pydantic BaseModel, try to parse it
            try:
                if isinstance(type_, type) and issubclass(type_, BaseModel) and isinstance(result, dict):
                    return type_.model_validate(result)  # type: ignore
            except Exception:
                pass

        return result


class JsonCoder(Coder):
    """JSON-based coder with customizable encoder."""

    def __init__(self, default: Callable[[Any], Any] | None = None, object_hook: Callable[[dict], Any] | None = None):
        """Initialize JsonCoder with optional custom handlers.

        Args:
            default: Function to handle non-serializable types
            object_hook: Custom object hook for decoding
        """
        self.custom_default = default
        self.object_hook = object_hook or globals()["object_hook"]  # Use the module-level object_hook

    def encode(self, value: Any) -> bytes:
        # Handle None directly to ensure proper encoding
        if value is None:
            return json.dumps({"_spec_type": "none"}).encode()

        # Create a custom encoder that uses our default function
        if self.custom_default:

            class CustomEncoder(JsonEncoder):
                def default(self_inner, obj):  # noqa: N805
                    try:
                        return self.custom_default(obj)
                    except TypeError:
                        return super().default(obj)

            return json.dumps(value, cls=CustomEncoder).encode()
        else:
            return json.dumps(value, cls=JsonEncoder).encode()

    def decode(self, value: bytes) -> Any:
        # explicitly decode from UTF-8 bytes first
        return json.loads(value.decode(), object_hook=self.object_hook)


class PickleCoder(Coder):
    """Pickle-based coder for complex Python objects."""

    def __init__(self, protocol: int | None = None):
        """Initialize PickleCoder with optional protocol version.

        Args:
            protocol: Pickle protocol version to use
        """
        self.protocol = protocol

    def encode(self, value: Any) -> bytes:
        return pickle.dumps(value, protocol=self.protocol)

    def decode(self, value: bytes) -> Any:
        return pickle.loads(value)

    def decode_as_type(self, value: bytes, *, type_: _T | None) -> Any:
        # Pickle already produces the correct type on decoding
        return self.decode(value)


class OrjsonCoder(Coder):
    """Fast JSON coder using orjson library.

    Requires: pip install pydantic-typed-cache[orjson]
    """

    def __init__(self, default: Callable[[Any], Any] | None = None, option: int | None = None):
        """Initialize OrjsonCoder with optional custom default function.

        Args:
            default: Function to handle non-serializable types. It will be called
                    recursively for nested structures. Should return a serializable
                    value or raise TypeError.
            option: orjson options flags (e.g., orjson.OPT_INDENT_2)
        """
        self.custom_default = default
        self.option = option
        self._orjson = None  # Lazy import

    def _ensure_orjson(self):
        """Lazy import orjson."""
        if self._orjson is None:
            try:
                import orjson

                self._orjson = orjson
            except ImportError as e:
                raise ImportError(
                    "OrjsonCoder requires orjson to be installed. "
                    "Install it with: pip install pydantic-typed-cache[orjson]"
                ) from e
        return self._orjson

    def _default_handler(self, obj: Any) -> Any:
        """Default handler that processes nested structures and custom types."""
        # First try custom handler if provided
        if self.custom_default is not None:
            try:
                return self.custom_default(obj)
            except TypeError:
                pass  # Fall through to built-in handling

        # Built-in handling for Pydantic models
        if isinstance(obj, BaseModel):
            return obj.model_dump()

        # Let orjson handle the error for truly unserializable types
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

    def encode(self, value: Any) -> bytes:
        orjson = self._ensure_orjson()

        # Special handling for None to distinguish from cache miss
        if value is None:
            return orjson.dumps({"_spec_type": "none"}, option=self.option)

        # Use the default handler for custom types and nested structures
        return orjson.dumps(value, default=self._default_handler, option=self.option)

    def decode(self, value: bytes) -> Any:
        orjson = self._ensure_orjson()

        # orjson.loads returns dict directly (not str)
        data = orjson.loads(value)

        # Handle our special None encoding
        if isinstance(data, dict) and data.get("_spec_type") == "none":
            return None

        return data
