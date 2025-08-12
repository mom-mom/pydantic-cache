import datetime
import json
import pickle  # nosec:B403
from decimal import Decimal
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Optional,
    TypeVar,
    Union,
    overload,
)

import pendulum
from pydantic import BaseModel
from pydantic.json import pydantic_encoder

_T = TypeVar("_T", bound=type)

CONVERTERS: Dict[str, Callable[[str], Any]] = {
    "date": lambda x: pendulum.parse(x, exact=True),
    "datetime": lambda x: pendulum.parse(x, exact=True),
    "decimal": Decimal,
}


class JsonEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, datetime.datetime):
            return {"val": str(o), "_spec_type": "datetime"}
        elif isinstance(o, datetime.date):
            return {"val": str(o), "_spec_type": "date"}
        elif isinstance(o, Decimal):
            return {"val": str(o), "_spec_type": "decimal"}
        elif isinstance(o, BaseModel):
            return o.model_dump()
        else:
            try:
                return pydantic_encoder(o)
            except TypeError:
                return super().default(o)


def object_hook(obj: Any) -> Any:
    _spec_type = obj.get("_spec_type")
    if not _spec_type:
        return obj

    if _spec_type in CONVERTERS:
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
    def decode_as_type(cls, value: bytes, *, type_: _T) -> _T:
        ...

    @overload
    @classmethod
    def decode_as_type(cls, value: bytes, *, type_: None) -> Any:
        ...

    @classmethod
    def decode_as_type(cls, value: bytes, *, type_: Optional[_T]) -> Union[_T, Any]:
        """Decode value to the specific given type
        
        The default implementation tries to convert the value using Pydantic if it's a BaseModel.
        """
        result = cls.decode(value)
        
        if type_ is not None:
            # If type_ is a Pydantic BaseModel, try to parse it
            try:
                if isinstance(type_, type) and issubclass(type_, BaseModel):
                    if isinstance(result, dict):
                        return type_.model_validate(result)  # type: ignore
            except Exception:
                pass
        
        return result


class JsonCoder(Coder):
    @classmethod
    def encode(cls, value: Any) -> bytes:
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
        return pickle.loads(value)  # noqa: S301

    @classmethod
    def decode_as_type(cls, value: bytes, *, type_: Optional[_T]) -> Any:
        # Pickle already produces the correct type on decoding
        return cls.decode(value)