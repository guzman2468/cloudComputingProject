"""Unit tests for in-memory rate limiting."""

import pytest
from fastapi import HTTPException

from backend.core.rate_limit import InMemoryRateLimiter


def test_rate_limiter_allows_under_limit():
    limiter = InMemoryRateLimiter()
    for _ in range(5):
        limiter.check("test-key", limit=5, window_seconds=60)


def test_rate_limiter_blocks_and_sets_retry_after():
    limiter = InMemoryRateLimiter()
    for _ in range(3):
        limiter.check("block-key", limit=3, window_seconds=60)

    with pytest.raises(HTTPException) as exc_info:
        limiter.check("block-key", limit=3, window_seconds=60)

    assert exc_info.value.status_code == 429
    assert "Retry-After" in exc_info.value.headers
    assert int(exc_info.value.headers["Retry-After"]) > 0


def test_rate_limiter_active_count():
    limiter = InMemoryRateLimiter()
    limiter.check("user:1", limit=5, window_seconds=60)
    limiter.check("user:2", limit=5, window_seconds=60)
    limiter.check("admin:1", limit=5, window_seconds=60)

    assert limiter.active_count("user:") == 2
    assert limiter.active_count("admin:") == 1
    assert limiter.active_count("other:") == 0

