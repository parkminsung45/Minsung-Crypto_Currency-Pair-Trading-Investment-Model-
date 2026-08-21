"""업비트 REST API용 토큰버킷 레이트리미터.

업비트는 엔드포인트 그룹별로 초당 요청 한도가 다르다(시세 조회 그룹 기준 초당 약 10회).
보수적으로 기본값을 낮게 잡는다.
"""
from __future__ import annotations

import asyncio
import time


class TokenBucketLimiter:
    def __init__(self, rate_per_sec: float = 8.0, burst: int = 8) -> None:
        self._rate = rate_per_sec
        self._capacity = burst
        self._tokens = float(burst)
        self._updated_at = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            while True:
                now = time.monotonic()
                elapsed = now - self._updated_at
                self._updated_at = now
                self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)

                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return

                wait = (1.0 - self._tokens) / self._rate
                await asyncio.sleep(wait)
