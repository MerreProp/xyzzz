# redis_cache.py
"""
Redis Caching System for HMO Analyser Phase 2
High-performance caching with smart invalidation
"""

import redis.asyncio as redis
import json
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from functools import wraps
import pickle
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisCache:
    """High-performance Redis cache manager with async support"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.sync_client = None
        self.async_client = None
        self.default_ttl = 300  # 5 minutes default
        
    async def connect_async(self):
        """Initialize async Redis connection"""
        if not self.async_client:
            self.async_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20
            )
            logger.info("✅ Redis async connection established")
        return self.async_client
    
    def connect_sync(self):
        """Initialize sync Redis connection"""
        if not self.sync_client:
            self.sync_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20
            )
            logger.info("✅ Redis sync connection established")
        return self.sync_client
    
    def generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate consistent cache keys"""
        # Create a hash of arguments for consistent keys
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()[:12]
        return f"hmo_cache:{prefix}:{key_hash}"
    
    async def get_async(self, key: str) -> Optional[Any]:
        """Get cached value asynchronously"""
        try:
            client = await self.connect_async()
            cached_data = await client.get(key)
            
            if cached_data:
                try:
                    # Try JSON decode first (for simple data)
                    data = json.loads(cached_data)
                    logger.info(f"📦 Cache HIT (async): {key[:50]}...")
                    return data
                except json.JSONDecodeError:
                    # Fallback to pickle for complex objects
                    data = pickle.loads(cached_data.encode('latin1'))
                    logger.info(f"📦 Cache HIT (async/pickle): {key[:50]}...")
                    return data
            
            logger.info(f"❌ Cache MISS (async): {key[:50]}...")
            return None
            
        except Exception as e:
            logger.error(f"Redis async get error: {e}")
            return None
    
    async def set_async(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set cached value asynchronously"""
        try:
            client = await self.connect_async()
            ttl = ttl or self.default_ttl
            
            # Try JSON encode first (faster and more readable)
            try:
                serialized = json.dumps(value, default=str)
                await client.setex(key, ttl, serialized)
            except (TypeError, ValueError):
                # Fallback to pickle for complex objects
                serialized = pickle.dumps(value).decode('latin1')
                await client.setex(key, ttl, serialized)
            
            logger.info(f"💾 Cache SET (async): {key[:50]}... (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Redis async set error: {e}")
            return False
    
    def get_sync(self, key: str) -> Optional[Any]:
        """Get cached value synchronously"""
        try:
            client = self.connect_sync()
            cached_data = client.get(key)
            
            if cached_data:
                try:
                    data = json.loads(cached_data)
                    logger.info(f"📦 Cache HIT (sync): {key[:50]}...")
                    return data
                except json.JSONDecodeError:
                    data = pickle.loads(cached_data.encode('latin1'))
                    logger.info(f"📦 Cache HIT (sync/pickle): {key[:50]}...")
                    return data
            
            logger.info(f"❌ Cache MISS (sync): {key[:50]}...")
            return None
            
        except Exception as e:
            logger.error(f"Redis sync get error: {e}")
            return None
    
    def set_sync(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set cached value synchronously"""
        try:
            client = self.connect_sync()
            ttl = ttl or self.default_ttl
            
            try:
                serialized = json.dumps(value, default=str)
                client.setex(key, ttl, serialized)
            except (TypeError, ValueError):
                serialized = pickle.dumps(value).decode('latin1')
                client.setex(key, ttl, serialized)
            
            logger.info(f"💾 Cache SET (sync): {key[:50]}... (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Redis sync set error: {e}")
            return False
    
    async def delete_async(self, pattern: str) -> int:
        """Delete cache keys by pattern"""
        try:
            client = await self.connect_async()
            keys = await client.keys(pattern)
            if keys:
                deleted = await client.delete(*keys)
                logger.info(f"🗑️ Cache DELETE (async): {deleted} keys matching {pattern}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Redis async delete error: {e}")
            return 0
    
    def delete_sync(self, pattern: str) -> int:
        """Delete cache keys by pattern (sync)"""
        try:
            client = self.connect_sync()
            keys = client.keys(pattern)
            if keys:
                deleted = client.delete(*keys)
                logger.info(f"🗑️ Cache DELETE (sync): {deleted} keys matching {pattern}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Redis sync delete error: {e}")
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            client = await self.connect_async()
            info = await client.info('memory')
            keyspace_info = await client.info('keyspace')
            
            # Count our cache keys
            our_keys = await client.keys("hmo_cache:*")
            
            return {
                "total_hmo_cache_keys": len(our_keys),
                "memory_used_mb": round(info.get('used_memory', 0) / 1024 / 1024, 2),
                "memory_peak_mb": round(info.get('used_memory_peak', 0) / 1024 / 1024, 2),
                "keyspace_hits": keyspace_info.get('keyspace_hits', 0),
                "keyspace_misses": keyspace_info.get('keyspace_misses', 0),
                "cache_hit_rate": self._calculate_hit_rate(keyspace_info),
                "connected": True
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "connected": False,
                "error": str(e)
            }
    
    def _calculate_hit_rate(self, keyspace_info: Dict) -> float:
        """Calculate cache hit rate percentage"""
        hits = keyspace_info.get('keyspace_hits', 0)
        misses = keyspace_info.get('keyspace_misses', 0)
        total = hits + misses
        
        if total == 0:
            return 0.0
        
        return round((hits / total) * 100, 2)

# Global cache instance
cache = RedisCache()

# Decorator for caching function results
def cache_result(ttl: int = 300, key_prefix: str = "func"):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache.generate_cache_key(key_prefix, func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_result = await cache.get_async(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache.set_async(cache_key, result, ttl)
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache.generate_cache_key(key_prefix, func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache.get_sync(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set_sync(cache_key, result, ttl)
            return result
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# Smart cache invalidation utilities
class CacheInvalidator:
    """Handles intelligent cache invalidation"""
    
    @staticmethod
    async def invalidate_property_caches(property_id: str):
        """Invalidate all caches related to a specific property"""
        patterns_to_clear = [
            f"hmo_cache:api:properties:*",      # FIXED: Added api: prefix
            f"hmo_cache:api:analytics:*",       # FIXED: Added api: prefix
            f"hmo_cache:api:search:*",          # FIXED: Added api: prefix
            f"hmo_cache:api:*",                 # FIXED: Catch-all for API caches
        ]
        
        total_deleted = 0
        for pattern in patterns_to_clear:
            deleted = await cache.delete_async(pattern)
            total_deleted += deleted
        
        logger.info(f"🔄 Invalidated {total_deleted} cache keys for property {property_id}")
        return total_deleted
    
    @staticmethod
    async def invalidate_analytics_caches():
        """Invalidate analytics and dashboard caches"""
        patterns_to_clear = [
            "hmo_cache:api:analytics:*",    # FIXED: Added api: prefix
            "hmo_cache:api:dashboard:*",    # FIXED: Added api: prefix
            "hmo_cache:api:stats:*"         # FIXED: Added api: prefix
        ]
        
        total_deleted = 0
        for pattern in patterns_to_clear:
            deleted = await cache.delete_async(pattern)
            total_deleted += deleted
        
        logger.info(f"📊 Invalidated {total_deleted} analytics cache keys")
        return total_deleted
    
    @staticmethod
    async def invalidate_contact_caches(user_id: str):
        """Invalidate contact-related caches for a user"""
        patterns_to_clear = [
            f"hmo_cache:contacts:{user_id}*",
            f"hmo_cache:contact_lists:{user_id}*"
        ]
        
        total_deleted = 0
        for pattern in patterns_to_clear:
            deleted = await cache.delete_async(pattern)
            total_deleted += deleted
        
        logger.info(f"👥 Invalidated {total_deleted} contact cache keys for user {user_id}")
        return total_deleted

# Health check for Redis
async def check_redis_health() -> Dict[str, Any]:
    """Check Redis connection and health"""
    try:
        client = await cache.connect_async()
        await client.ping()
        
        # Get basic stats
        stats = await cache.get_cache_stats()
        
        return {
            "status": "healthy",
            "connected": True,
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Initialize cache on import
async def init_cache():
    """Initialize cache connections"""
    try:
        await cache.connect_async()
        cache.connect_sync()
        logger.info("🚀 Redis cache system initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Redis cache: {e}")

# Auto-run initialization
if __name__ == "__main__":
    asyncio.run(init_cache())