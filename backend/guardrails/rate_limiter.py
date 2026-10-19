from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Callable, Optional

from fastapi import HTTPException, Request

import config

logger = logging.getLogger(__name__)


@dataclass
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    reset_after_seconds: int


class SlidingWindowRateLimiter:
    """Thread-safe async in-memory sliding window rate limiter."""

    def __init__(self) -> None:
        self._buckets: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()
        self._last_cleanup = time.time()

    async def check(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        """Check if request is allowed under the sliding window limit."""
        now = time.time()
        cutoff = now - window_seconds

        async with self._lock:
            # Periodic background cleanup of stale keys (every 5 minutes)
            if now - self._last_cleanup > 300:
                self._cleanup_stale_buckets(now)
                self._last_cleanup = now

            timestamps = self._buckets[key]

            # Evict timestamps outside the sliding window
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()

            current_count = len(timestamps)

            if current_count >= limit:
                # Oldest timestamp in window determines when the next slot frees up
                oldest = timestamps[0]
                reset_after = max(1, int(oldest + window_seconds - now))
                return RateLimitResult(
                    allowed=False,
                    limit=limit,
                    remaining=0,
                    reset_after_seconds=reset_after,
                )

            # Record this request
            timestamps.append(now)
            remaining = limit - (current_count + 1)
            reset_after = window_seconds

            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=remaining,
                reset_after_seconds=reset_after,
            )

    def _cleanup_stale_buckets(self, now: float) -> None:
        """Removes bucket entries with no activity in the last 10 minutes."""
        stale_threshold = now - 600
        keys_to_remove = []
        for key, timestamps in self._buckets.items():
            while timestamps and timestamps[0] <= stale_threshold:
                timestamps.popleft()
            if not timestamps:
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del self._buckets[key]

    async def reset(self) -> None:
        """Resets all buckets (used mainly for tests)."""
        async with self._lock:
            self._buckets.clear()


# Global Singleton Limiter Instance
_rate_limiter = SlidingWindowRateLimiter()


def get_client_identifier(request: Request) -> str:
    """Use the ASGI peer, normalized only by a configured trusted proxy server.

    Never trust caller-supplied forwarding headers or session IDs for quotas.
    """
    return request.client.host if request.client else "unknown"


def rate_limit(limit: int, window_seconds: int = 60) -> Callable:
    """FastAPI dependency to enforce rate limits per client on specific routes."""

    async def _rate_limit_dependency(request: Request) -> None:
        if not getattr(config, "ENABLE_RATE_LIMITING", True):
            return

        client_id = get_client_identifier(request)
        endpoint = request.url.path
        rate_key = f"{client_id}:{endpoint}"

        result = await _rate_limiter.check(rate_key, limit, window_seconds)

        if not result.allowed:
            logger.warning(
                "Rate limit exceeded for %s on %s (Limit: %d/%ds)",
                client_id,
                endpoint,
                limit,
                window_seconds,
            )
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Try again in {result.reset_after_seconds} seconds.",
                headers={
                    "Retry-After": str(result.reset_after_seconds),
                    "X-RateLimit-Limit": str(result.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(result.reset_after_seconds),
                },
            )

    return _rate_limit_dependency
