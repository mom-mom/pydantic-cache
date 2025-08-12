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
    @classmethod
    def encode(cls, value: Any) -> bytes:
        raise NotImplementedError

    @classmethod
    def decode(cls, value: bytes) -> Any:
        raise NotImplementedError

    @overload
    @classmethod
    def decode_as_type(cls, value: bytes, *, type_: _T) -> _T: ...

    @overload
    @classmethod
    def decode_as_type(cls, value: bytes, *, type_: None) -> Any: ...

    @classmethod
    def decode_as_type(cls, value: bytes, *, type_: _T | None) -> _T | Any:
        """Decode value to the specific given type

        The default implementation tries to convert the value using Pydantic if it's a BaseModel.
        """
        result = cls.decode(value)

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
    @classmethod
    def encode(cls, value: Any) -> bytes:
        # Handle None directly to ensure proper encoding
        if value is None:
            return json.dumps({"_spec_type": "none"}).encode()
        return json.dumps(value, cls=JsonEncoder).encode()

    @classmethod
    def decode(cls, value: bytes) -> Any:
        # explicitly decode from UTF-8 bytes first
        return json.loads(value.decode(), object_hook=object_hook)


class PickleCoder(Coder):
    @classmethod
    def encode(cls, value: Any) -> bytes:
        return pickle.dumps(value)

    @classmethod
    def decode(cls, value: bytes) -> Any:
        return pickle.loads(value)

    @classmethod
    def decode_as_type(cls, value: bytes, *, type_: _T | None) -> Any:
        # Pickle already produces the correct type on decoding
        return cls.decode(value)


class OrjsonCoder(Coder):
    """Fast JSON coder using orjson library.

    Requires: pip install pydantic-typed-cache[orjson]
    """

    @classmethod
    def encode(cls, value: Any) -> bytes:
        try:
            import orjson
        except ImportError as e:
            raise ImportError(
                "OrjsonCoder requires orjson to be installed. "
                "Install it with: pip install pydantic-typed-cache[orjson]"
            ) from e

        # orjson handles Pydantic models, datetime, etc. automatically
        # But we need special handling for None to distinguish from cache miss
        if value is None:
            return orjson.dumps({"_spec_type": "none"})

        # Convert Pydantic models to dict for consistent serialization
        if isinstance(value, BaseModel):
            return orjson.dumps(value.model_dump())

        return orjson.dumps(value)

    @classmethod
    def decode(cls, value: bytes) -> Any:
        try:
            import orjson
        except ImportError as e:
            raise ImportError(
                "OrjsonCoder requires orjson to be installed. "
                "Install it with: pip install pydantic-typed-cache[orjson]"
            ) from e

        # orjson.loads returns dict directly (not str)
        data = orjson.loads(value)

        # Handle our special None encoding
        if isinstance(data, dict) and data.get("_spec_type") == "none":
            return None

        return data
