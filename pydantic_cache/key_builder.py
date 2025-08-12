import hashlib
from typing import Any, Callable, Dict, Tuple


def default_key_builder(
    func: Callable[..., Any],
    namespace: str = "",
    *,
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
) -> str:
    cache_key = hashlib.md5(  # noqa: S324
        f"{func.__module__}:{func.__name__}:{args}:{kwargs}".encode()
    ).hexdigest()
    return f"{namespace}:{cache_key}"