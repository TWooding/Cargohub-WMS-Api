import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, status


class RateLimiter:
    """Sliding window per key, in-memory. Per proces: gebruik bij meerdere workers een
    gedeelde store (bv. Redis) achter dezelfde interface."""

    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str, limit: int, window: int) -> int:
        """Registreert een poging. 0 = toegestaan, anders seconden tot opnieuw proberen."""
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and q[0] <= now - window:
                q.popleft()
            if len(q) >= limit:
                return max(1, int(q[0] + window - now) + 1)
            q.append(now)
            return 0

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = RateLimiter()


def enforce(key: str, limit: int, window: int) -> None:
    retry = limiter.hit(key, limit, window)
    if retry:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "too many requests", headers={"Retry-After": str(retry)}
        )
