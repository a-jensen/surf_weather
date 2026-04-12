from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone
from typing import Any

_DEFAULT_TTL_SECONDS = 900  # 15 minutes


class _CacheEntry:
    __slots__ = ("value", "expires_at")

    def __init__(self, value: Any, ttl_seconds: float) -> None:
        self.value = value
        self.expires_at = datetime.now(tz=timezone.utc) + timedelta(seconds=ttl_seconds)

    def is_fresh(self) -> bool:
        return datetime.now(tz=timezone.utc) < self.expires_at


class CachingAggregator:
    """Wraps an Aggregator and caches results with a TTL. Thread-safe."""

    def __init__(self, aggregator: Any, ttl_seconds: float = _DEFAULT_TTL_SECONDS) -> None:
        self._aggregator = aggregator
        self._ttl = ttl_seconds
        self._lock = threading.Lock()
        self._summaries_cache: _CacheEntry | None = None
        self._detail_cache: dict[str, _CacheEntry] = {}

    def get_all_summaries(self):
        with self._lock:
            if self._summaries_cache is not None and self._summaries_cache.is_fresh():
                return self._summaries_cache.value
        # Fetch outside the lock so slow upstream calls don't block other cache reads.
        result = self._aggregator.get_all_summaries()
        with self._lock:
            if self._summaries_cache is None or not self._summaries_cache.is_fresh():
                self._summaries_cache = _CacheEntry(result, self._ttl)
            return self._summaries_cache.value

    def get_detail(self, lake_id: str):
        with self._lock:
            entry = self._detail_cache.get(lake_id)
            if entry is not None and entry.is_fresh():
                return entry.value
        # KeyError from the inner aggregator propagates naturally; no cache entry is written.
        result = self._aggregator.get_detail(lake_id)
        with self._lock:
            entry = self._detail_cache.get(lake_id)
            if entry is None or not entry.is_fresh():
                self._detail_cache[lake_id] = _CacheEntry(result, self._ttl)
            return self._detail_cache[lake_id].value
