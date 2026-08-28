from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import status
import time
from typing import Dict
from app.core.logging import get_logger

logger = get_logger(__name__)


class InMemoryRateLimiter(BaseHTTPMiddleware):
    """Simple in-memory per-IP token bucket rate limiter.

    Not distributed — suitable for single-instance deployments or basic protection.
    """

    def __init__(self, app, rate_per_minute: int = 60):
        super().__init__(app)
        self._rate = max(1, int(rate_per_minute))
        self._window = 60
        # store: ip -> (tokens, last_timestamp)
        self._buckets: Dict[str, tuple[float, float]] = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        bucket = self._buckets.get(client_ip, (self._rate, now))
        tokens, last = bucket
        # refill
        elapsed = now - last
        refill = (elapsed / self._window) * self._rate
        tokens = min(self._rate, tokens + refill)
        if tokens >= 1:
            tokens -= 1
            self._buckets[client_ip] = (tokens, now)
            return await call_next(request)
        # rate limited
        self._buckets[client_ip] = (tokens, now)
        logger.warning("Rate limit exceeded for %s", client_ip)
        return Response(content="Rate limit exceeded", status_code=status.HTTP_429_TOO_MANY_REQUESTS)
