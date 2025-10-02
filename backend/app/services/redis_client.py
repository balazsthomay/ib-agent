"""Redis client wrapper using Upstash Redis."""

from typing import Any

from upstash_redis.asyncio import Redis

from app.config import settings


class RedisClient:
    """
    Redis client wrapper for Upstash Redis.

    Upstash Redis uses a REST API over HTTPS, making it ideal for serverless environments.
    """

    def __init__(self):
        """Initialize Upstash Redis client from environment variables."""
        self.client = Redis(
            url=settings.upstash_redis_url,
            token=settings.upstash_redis_token,
        )

    async def get(self, key: str) -> str | None:
        """Get value by key."""
        return await self.client.get(key)

    async def set(
        self,
        key: str,
        value: Any,
        ex: int | None = None,
        px: int | None = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """
        Set key to value.

        Args:
            key: Redis key
            value: Value to store
            ex: Expiration in seconds
            px: Expiration in milliseconds
            nx: Only set if key doesn't exist
            xx: Only set if key exists

        Returns:
            True if successful
        """
        return await self.client.set(key, value, ex=ex, px=px, nx=nx, xx=xx)

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys."""
        return await self.client.delete(*keys)

    async def exists(self, *keys: str) -> int:
        """Check if keys exist."""
        return await self.client.exists(*keys)

    async def expire(self, key: str, seconds: int) -> bool:
        """Set key expiration in seconds."""
        return await self.client.expire(key, seconds)

    async def ttl(self, key: str) -> int:
        """Get time to live for key in seconds."""
        return await self.client.ttl(key)

    async def incr(self, key: str) -> int:
        """Increment key by 1."""
        return await self.client.incr(key)

    async def decr(self, key: str) -> int:
        """Decrement key by 1."""
        return await self.client.decr(key)

    async def hget(self, key: str, field: str) -> str | None:
        """Get hash field value."""
        return await self.client.hget(key, field)

    async def hset(self, key: str, field: str, value: Any) -> int:
        """Set hash field value."""
        return await self.client.hset(key, field, value)

    async def hgetall(self, key: str) -> dict:
        """Get all hash fields and values."""
        return await self.client.hgetall(key)

    async def hdel(self, key: str, *fields: str) -> int:
        """Delete hash fields."""
        return await self.client.hdel(key, *fields)

    async def lpush(self, key: str, *values: Any) -> int:
        """Push values to list (left)."""
        return await self.client.lpush(key, *values)

    async def rpush(self, key: str, *values: Any) -> int:
        """Push values to list (right)."""
        return await self.client.rpush(key, *values)

    async def lpop(self, key: str) -> str | None:
        """Pop value from list (left)."""
        return await self.client.lpop(key)

    async def rpop(self, key: str) -> str | None:
        """Pop value from list (right)."""
        return await self.client.rpop(key)

    async def lrange(self, key: str, start: int, stop: int) -> list:
        """Get range of list elements."""
        return await self.client.lrange(key, start, stop)

    async def sadd(self, key: str, *members: Any) -> int:
        """Add members to set."""
        return await self.client.sadd(key, *members)

    async def smembers(self, key: str) -> set:
        """Get all set members."""
        return await self.client.smembers(key)

    async def srem(self, key: str, *members: Any) -> int:
        """Remove members from set."""
        return await self.client.srem(key, *members)

    async def pipeline(self):
        """Create pipeline for batch operations."""
        return self.client.pipeline()

    async def close(self):
        """Close Redis connection (cleanup if needed)."""
        # Upstash Redis is connectionless, but we keep this for interface consistency
        pass


# Singleton instance
redis_client = RedisClient()
