"""Process-local sliding-window limiter for authentication attempts."""

import asyncio
from collections import defaultdict, deque
from time import monotonic

from app.common.application.errors import BusinessException


class AuthRateLimiter:
    """Limit repeated authentication attempts in the single-worker deployment."""

    def __init__(self, *, max_attempts: int, window_seconds: int) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts: defaultdict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    def _prune(self, attempts: deque[float], now: float) -> None:
        threshold = now - self.window_seconds
        while attempts and attempts[0] <= threshold:
            attempts.popleft()

    @staticmethod
    def _raise_rate_limit() -> None:
        raise BusinessException(
            status_code=429,
            code="AUTH_TOO_MANY_ATTEMPTS",
            message="인증 시도가 너무 많습니다. 잠시 후 다시 시도해 주세요.",
        )

    async def ensure_allowed(self, key: str) -> None:
        async with self._lock:
            attempts = self._attempts[key]
            self._prune(attempts, monotonic())
            if len(attempts) >= self.max_attempts:
                self._raise_rate_limit()

    async def record_attempt(self, key: str) -> None:
        async with self._lock:
            now = monotonic()
            attempts = self._attempts[key]
            self._prune(attempts, now)
            if len(attempts) >= self.max_attempts:
                self._raise_rate_limit()
            attempts.append(now)

    async def record_failure(self, key: str) -> None:
        async with self._lock:
            now = monotonic()
            attempts = self._attempts[key]
            self._prune(attempts, now)
            attempts.append(now)

    async def reset(self, key: str) -> None:
        async with self._lock:
            self._attempts.pop(key, None)
