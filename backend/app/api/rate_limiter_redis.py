from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import status
from typing import Optional
import asyncio
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class RedisRateLimiter(BaseHTTPMiddleware):
    """Redis-backed simple rate limiter using a fixed-window counter per client IP.

    This implementation uses Redis INCR with EXPIRE to enforce per-minute limits.
    It's not a full token-bucket but is sufficient and efficient for distributed
    rate limiting across multiple instances.
    """

    def __init__(self, app, redis_url: Optional[str] = None, rate_per_minute: int = 600, prefix: str = "rl:"):
        super().__init__(app)
        self._redis_url = redis_url or get_settings().redis_url
        self._rate = max(1, int(rate_per_minute))
        self._prefix = prefix
        # Use lazy import to avoid hard dependency at import time
        self._client = None
        self._lock = asyncio.Lock()

    async def _ensure_client(self):
        if self._client is not None:
            return
        async with self._lock:
            if self._client is not None:
                return
            try:
                import redis.asyncio as aioredis
            except Exception as exc:
                logger.warning("redis.asyncio not available: %s", exc)
                self._client = None
                return
            try:
                self._client = aioredis.from_url(self._redis_url)
            except Exception as exc:
                logger.error("Failed to create redis client: %s", exc)
                self._client = None

    async def dispatch(self, request: Request, call_next):
        await self._ensure_client()
        if not self._client:
            # Fallback to allowing traffic when Redis is not available — better than failing open
            logger.warning("RedisRateLimiter: redis client unavailable; allowing request")
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"{self._prefix}{client_ip}:{int(__import__('time').time() // 60)}"
        try:
            # INCR and set EXPIRE if first time
            val = await self._client.incr(key)
            if val == 1:
                await self._client.expire(key, 61)
            if val > self._rate:
                logger.debug("RedisRateLimiter: rate-limited %s count=%s limit=%s", client_ip, val, self._rate)
                return Response(content="Rate limit exceeded", status_code=status.HTTP_429_TOO_MANY_REQUESTS)
        except Exception as exc:
            logger.error("RedisRateLimiter encountered an error: %s", exc)
            # In case of Redis errors, allow request to avoid DoS
            return await call_next(request)

        return await call_next(request)


class TokenBucketRedisRateLimiter(BaseHTTPMiddleware):
    """Distributed token-bucket implemented with a small Redis Lua script.

    This implementation stores a per-client key with fields `tokens` and `ts` and
    refills tokens based on elapsed time. It is atomic due to Lua eval.

    Keys: prefix + client_id

    Args to script: now_seconds, capacity, refill_rate_per_sec, requested
    Returns: 1 if allowed, 0 if not allowed
    """

    _LUA = r"""
    local key = KEYS[1]
    local now = tonumber(ARGV[1])
    local capacity = tonumber(ARGV[2])
    local refill_per_sec = tonumber(ARGV[3])
    local requested = tonumber(ARGV[4])

    local data = redis.call('HMGET', key, 'tokens', 'ts')
    local tokens = tonumber(data[1]) or capacity
    local ts = tonumber(data[2]) or 0
    local delta = math.max(0, now - ts)
    local added = delta * refill_per_sec
    tokens = math.min(capacity, tokens + added)
    local allowed = 0
    if tokens >= requested then
      tokens = tokens - requested
      allowed = 1
    end
    redis.call('HMSET', key, 'tokens', tokens, 'ts', now)
    redis.call('EXPIRE', key, 3600)
    return allowed
    """

    def __init__(self, app, redis_url: Optional[str] = None, capacity: int = 600, refill_per_minute: int = 600, prefix: str = "tb:"):
        super().__init__(app)
        self._redis_url = redis_url or get_settings().redis_url
        self._capacity = max(1, int(capacity))
        self._refill_per_minute = max(1, int(refill_per_minute))
        # refill per second float
        self._refill_per_sec = float(self._refill_per_minute) / 60.0
        self._prefix = prefix
        self._client = None
        self._lock = asyncio.Lock()
        self._script_sha = None

    async def _ensure_client(self):
        if self._client is not None:
            return
        async with self._lock:
            if self._client is not None:
                return
            try:
                import redis.asyncio as aioredis
            except Exception as exc:
                logger.warning("redis.asyncio not available for TokenBucket: %s", exc)
                self._client = None
                return
            try:
                self._client = aioredis.from_url(self._redis_url)
            except Exception as exc:
                logger.error("Failed to create redis client for TokenBucket: %s", exc)
                self._client = None

    async def dispatch(self, request: Request, call_next):
        await self._ensure_client()
        if not self._client:
            logger.warning("TokenBucketRedisRateLimiter: redis client unavailable; allowing request")
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        key = f"{self._prefix}{client_ip}"
        now = int(__import__("time").time())
        try:
            allowed = await self._client.eval(self._LUA, 1, key, now, self._capacity, self._refill_per_sec, 1)
            if not allowed:
                return Response(content="Rate limit exceeded", status_code=status.HTTP_429_TOO_MANY_REQUESTS)
        except Exception as exc:
            logger.error("TokenBucketRedisRateLimiter encountered an error: %s", exc)
            return await call_next(request)

        return await call_next(request)
