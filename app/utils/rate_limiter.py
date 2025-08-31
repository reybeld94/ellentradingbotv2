import time
from typing import Optional

import redis.asyncio as redis

from app.config import settings


class RateLimiter:
    """Simple sliding window rate limiter backed by Redis."""

    def __init__(self, redis_client: redis.Redis, limit: int = 60, window: int = 60):
        self.redis = redis_client
        self.limit = limit
        self.window = window

    async def is_allowed(self, key: str) -> bool:
        """Return True if the action for the given key is within the rate limit."""
        now = int(time.time())
        member = str(time.time_ns())  # ensure unique member per request
        async with self.redis.pipeline(transaction=True) as pipe:
            await (pipe
                   .zremrangebyscore(key, 0, now - self.window)
                   .zadd(key, {member: now})
                   .zcard(key)
                   .expire(key, self.window))
            _, _, count, _ = await pipe.execute()
        return count <= self.limit


_redis_client: Optional[redis.Redis] = None
_rate_limiter: Optional[RateLimiter] = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    return _redis_client


def get_rate_limiter() -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(get_redis())
    return _rate_limiter
