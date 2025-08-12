import hashlib
from collections.abc import Callable
from typing import Any


def default_key_builder(
    func: Callable[..., Any],
    namespace: str = "",
    *,
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> str:
    cache_key = hashlib.md5(f"{func.__module__}:{func.__name__}:{args}:{kwargs}".encode()).hexdigest()
    return f"{namespace}:{cache_key}"
