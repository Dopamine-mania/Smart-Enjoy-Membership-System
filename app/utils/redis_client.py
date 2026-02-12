"""Redis client utility."""
import redis
from typing import Optional
from app.config import settings


class RedisClient:
    """Redis client wrapper."""

    def __init__(self):
        self._client: Optional[redis.Redis] = None

    def connect(self):
        """Connect to Redis."""
        self._client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )

    def disconnect(self):
        """Disconnect from Redis."""
        if self._client:
            self._client.close()

    @property
    def client(self) -> redis.Redis:
        """Get Redis client."""
        if not self._client:
            self.connect()
        return self._client

    def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        return self.client.get(key)

    def set(self, key: str, value: str, ex: int = None) -> bool:
        """Set key-value with optional expiry in seconds."""
        return self.client.set(key, value, ex=ex)

    def delete(self, key: str) -> int:
        """Delete key."""
        return self.client.delete(key)

    def incr(self, key: str) -> int:
        """Increment key value."""
        return self.client.incr(key)

    def expire(self, key: str, seconds: int) -> bool:
        """Set key expiry."""
        return self.client.expire(key, seconds)

    def ttl(self, key: str) -> int:
        """Get key TTL in seconds."""
        return self.client.ttl(key)

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        return self.client.exists(key) > 0

    def setnx(self, key: str, value: str) -> bool:
        """Set key if not exists (for distributed lock)."""
        return self.client.setnx(key, value)


# Global Redis client instance
redis_client = RedisClient()
