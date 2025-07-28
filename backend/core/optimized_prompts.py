from typing import Any


class OptimizedPrompts:
    """
    Simple in-memory cache for optimized prompts, for dashboard statistics.
    """

    def __init__(self) -> None:
        self._cache: dict[str, Any] = {}
        self._cache_hits: int = 0
        self._cache_misses: int = 0

    def get(self, prompt: str) -> Any:
        if prompt in self._cache:
            self._cache_hits += 1
            return self._cache[prompt]
        self._cache_misses += 1
        return None

    def set(self, prompt: str, value: Any) -> None:
        self._cache[prompt] = value

    def clear(self) -> None:
        self._cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
