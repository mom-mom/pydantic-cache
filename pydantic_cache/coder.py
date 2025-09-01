import json
import pickle  # nosec:B403
import types
from typing import (
    Any,
    TypeVar,
    Union,
    get_args,
    get_origin,
    overload,
)

from pydantic import BaseModel
from pydantic_core import to_jsonable_python

_T = TypeVar("_T", bound=type)


class PydanticJsonEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Pydantic models and other special types.

    This can be subclassed to add custom serialization logic while preserving
    the default handling for BaseModel and other types.
    """

    def default(self, obj: Any) -> Any:
        """Default handler for non-serializable types."""
        # Handle Pydantic models
        if isinstance(obj, BaseModel):
            return obj.model_dump()

        # Try pydantic_core conversion
        try:
            return to_jsonable_python(obj)
        except TypeError:
            pass

        # Fall back to parent class default (will raise TypeError)
        return super().default(obj)


class Coder:
    """Base class for encoding/decoding cache values.

    The coder handles serialization/deserialization of Python objects to/from bytes
    for storage in cache. Type preservation is handled by TypeAdapter when type hints
    are available, not by the coder itself.

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
    """JSON-based coder using standard json library.

    Note: Type information is not preserved during encoding. Special types like
    datetime, date, and Decimal are converted to strings. Type restoration is handled
    by TypeAdapter when type hints are available on the cached function.
    """

    def __init__(self, encoder_class: type[json.JSONEncoder] | None = None):
        """Initialize JsonCoder with optional custom encoder class.

        Args:
            encoder_class: Custom JSONEncoder subclass. If not provided,
                          uses the default PydanticJsonEncoder class.
        """
        self.encoder_class = encoder_class or PydanticJsonEncoder

    def encode(self, value: Any) -> bytes:
        # Use actual JSON null for None values
        if value is None:
            return b"null"

        # Convert to JSON with the encoder class
        return json.dumps(value, cls=self.encoder_class, ensure_ascii=False).encode()

    def decode(self, value: bytes) -> Any:
        # JSON null becomes None automatically
        return json.loads(value)


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


class OrjsonCoder(JsonCoder):
    """Fast JSON coder using orjson library.

    Provides better performance than JsonCoder, especially for large datasets.
    Like JsonCoder, type information is not preserved - type restoration is handled
    by TypeAdapter when type hints are available.

    Requires: pip install pydantic-typed-cache[orjson]
    """

    def __init__(self, encoder_class: type[json.JSONEncoder] | None = None, option: int | None = None):
        """Initialize OrjsonCoder with optional custom encoder class.

        Args:
            encoder_class: Custom JSONEncoder subclass. If not provided,
                          uses the default PydanticJsonEncoder class.
            option: orjson options flags (e.g., orjson.OPT_INDENT_2)
        """
        super().__init__(encoder_class)
        self.encoder = self.encoder_class()
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

    def encode(self, value: Any) -> bytes:
        orjson = self._ensure_orjson()

        # Use actual JSON null for None values
        if value is None:
            return b"null"

        # Use orjson with default handler
        return orjson.dumps(value, default=self.encoder.default, option=self.option)

    def decode(self, value: bytes) -> Any:
        orjson = self._ensure_orjson()
        # orjson handles null -> None automatically
        return orjson.loads(value)
