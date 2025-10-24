import redis.asyncio as redis
import os
import logging

log = logging.getLogger(__name__)

class RedisClient:
    def __init__(self, url: str):
        self.url=url
        self._client = None
    
    async def get_client(self):
        """Get or create new redis client"""
        if self._client is None:
            self._client = await redis.from_url(
                self.url,
                encoding="utf-8",
                decode_responses=True
            )
            log.info(f"Redis client connected to {self.url}")
        return self._client
    
    async def store_diff(self, diff_id: str, diff_content: str, ttl: int = 3600) -> bool:
        """Store diff content with TTL(default 1 hour)"""
        try:
            client = await self.get_client()
            await client.setex(f"diff:{diff_id}", ttl, diff_content)
            log.info(f"Stored diff {diff_id}")
            return True
        except Exception as e:
            log.error(f"Failed to store diff {diff_id}: {e}")
            return False
        
    async def close(self):
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            log.info("Redis client closed")
        