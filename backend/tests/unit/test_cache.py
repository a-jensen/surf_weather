"""Tests for CachingAggregator."""
from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from surf_weather.services.cache import CachingAggregator


# ---------------------------------------------------------------------------
# Test double
# ---------------------------------------------------------------------------

class _FakeAggregator:
    """Controllable stub that records how many times each method was called."""

    def __init__(self, summaries=None, details=None):
        self.summaries_call_count = 0
        self.detail_call_count = 0
        self._summaries = summaries if summaries is not None else ["lake_a"]
        self._details = details or {}

    def get_all_summaries(self):
        self.summaries_call_count += 1
        return self._summaries

    def get_detail(self, lake_id: str):
        self.detail_call_count += 1
        if lake_id not in self._details:
            raise KeyError(lake_id)
        return self._details[lake_id]


# ---------------------------------------------------------------------------
# Summaries caching
# ---------------------------------------------------------------------------

class TestCachingSummaries:
    def test_first_call_fetches_from_delegate(self):
        fake = _FakeAggregator()
        cache = CachingAggregator(fake, ttl_seconds=60)
        cache.get_all_summaries()
        assert fake.summaries_call_count == 1

    def test_second_call_returns_cached(self):
        fake = _FakeAggregator()
        cache = CachingAggregator(fake, ttl_seconds=60)
        cache.get_all_summaries()
        cache.get_all_summaries()
        assert fake.summaries_call_count == 1

    def test_expired_cache_re_fetches(self):
        fake = _FakeAggregator()
        cache = CachingAggregator(fake, ttl_seconds=0.001)
        cache.get_all_summaries()
        time.sleep(0.05)
        cache.get_all_summaries()
        assert fake.summaries_call_count == 2

    def test_returns_same_object_when_cached(self):
        fake = _FakeAggregator()
        cache = CachingAggregator(fake, ttl_seconds=60)
        result1 = cache.get_all_summaries()
        result2 = cache.get_all_summaries()
        assert result1 is result2


# ---------------------------------------------------------------------------
# Detail caching
# ---------------------------------------------------------------------------

class TestCachingDetail:
    def test_first_call_fetches_from_delegate(self):
        fake = _FakeAggregator(details={"lake_a": "detail_a"})
        cache = CachingAggregator(fake, ttl_seconds=60)
        cache.get_detail("lake_a")
        assert fake.detail_call_count == 1

    def test_second_call_returns_cached(self):
        fake = _FakeAggregator(details={"lake_a": "detail_a"})
        cache = CachingAggregator(fake, ttl_seconds=60)
        cache.get_detail("lake_a")
        cache.get_detail("lake_a")
        assert fake.detail_call_count == 1

    def test_different_lakes_cached_separately(self):
        fake = _FakeAggregator(details={"lake_a": "detail_a", "lake_b": "detail_b"})
        cache = CachingAggregator(fake, ttl_seconds=60)
        cache.get_detail("lake_a")
        cache.get_detail("lake_b")
        assert fake.detail_call_count == 2

    def test_expired_detail_re_fetches(self):
        fake = _FakeAggregator(details={"lake_a": "detail_a"})
        cache = CachingAggregator(fake, ttl_seconds=0.001)
        cache.get_detail("lake_a")
        time.sleep(0.05)
        cache.get_detail("lake_a")
        assert fake.detail_call_count == 2

    def test_unknown_lake_raises_key_error(self):
        fake = _FakeAggregator(details={})
        cache = CachingAggregator(fake, ttl_seconds=60)
        with pytest.raises(KeyError):
            cache.get_detail("nonexistent")

    def test_returns_same_object_when_cached(self):
        fake = _FakeAggregator(details={"lake_a": "detail_a"})
        cache = CachingAggregator(fake, ttl_seconds=60)
        result1 = cache.get_detail("lake_a")
        result2 = cache.get_detail("lake_a")
        assert result1 is result2


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------

class TestCachingThreadSafety:
    def test_concurrent_summary_calls_do_not_corrupt_result(self):
        expected = ["lake_a", "lake_b", "lake_c"]
        fake = _FakeAggregator(summaries=expected)
        cache = CachingAggregator(fake, ttl_seconds=60)

        n_threads = 20
        barrier = threading.Barrier(n_threads)
        results = []

        def fetch():
            barrier.wait()
            results.append(cache.get_all_summaries())

        with ThreadPoolExecutor(max_workers=n_threads) as executor:
            futures = [executor.submit(fetch) for _ in range(n_threads)]
            for f in futures:
                f.result()

        assert len(results) == n_threads
        assert all(r == expected for r in results)
        # At most n_threads fetches, at least 1
        assert 1 <= fake.summaries_call_count <= n_threads
