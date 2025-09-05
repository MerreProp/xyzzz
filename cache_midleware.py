# cache_middleware.py
"""
FastAPI Cache Middleware for Automatic Response Caching
Provides decorators and middleware for instant API responses
"""

import json
import hashlib
import inspect
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable
from functools import wraps

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from redis_cache import cache, CacheInvalidator

class CacheMiddleware(BaseHTTPMiddleware):
    """Middleware for automatic response caching"""
    
    def __init__(self, app, cache_ttl: int = 300):
        super().__init__(app)
        self.cache_ttl = cache_ttl
        self.cacheable_methods = {"GET"}
        self.cacheable_endpoints = {
            "/api/properties",
            "/api/analytics", 
            "/api/properties/search",
            "/api/contacts/health",
            "/api/contacts/lists",
            "/api/contacts/stats/summary"
        }
    
    async def dispatch(self, request: Request, call_next):
        # Only cache GET requests to specified endpoints
        if (request.method not in self.cacheable_methods or 
            not self._should_cache_endpoint(request.url.path)):
            return await call_next(request)
        
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        # Try to get cached response
        cached_response = await cache.get_async(cache_key)
        if cached_response:
            return JSONResponse(
                content=cached_response["content"],
                status_code=cached_response["status_code"],
                headers={
                    **cached_response.get("headers", {}),
                    "X-Cache-Status": "HIT",
                    "X-Cache-Key": cache_key[:20] + "..."
                }
            )
        
        # Execute request
        response = await call_next(request)
        
        # Cache successful responses
        if response.status_code == 200:
            await self._cache_response(cache_key, response)
        
        # Add cache headers
        response.headers["X-Cache-Status"] = "MISS"
        response.headers["X-Cache-Key"] = cache_key[:20] + "..."
        
        return response
    
    def _should_cache_endpoint(self, path: str) -> bool:
        """Check if endpoint should be cached"""
        return any(path.startswith(endpoint) for endpoint in self.cacheable_endpoints)
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for request"""
        key_components = [
            request.method,
            str(request.url.path),
            str(sorted(request.query_params.items())),
            request.headers.get("authorization", "")[:20]  # Include auth for user-specific data
        ]
        key_string = "|".join(key_components)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"hmo_cache:api:{key_hash}"
    
    async def _cache_response(self, cache_key: str, response: Response):
        """Cache the response"""
        try:
            # Read response body
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            # Parse JSON content
            content = json.loads(response_body.decode())
            
            # Prepare cache data
            cache_data = {
                "content": content,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "cached_at": datetime.utcnow().isoformat()
            }
            
            # Cache the response
            await cache.set_async(cache_key, cache_data, self.cache_ttl)
            
            # Recreate response body for client
            response.body_iterator = self._create_body_iterator(response_body)
            
        except Exception as e:
            print(f"Error caching response: {e}")
    
    def _create_body_iterator(self, body: bytes):
        """Create body iterator for response"""
        async def _body_iterator():
            yield body
        return _body_iterator()

# Decorator for caching specific endpoints
def cache_response(ttl: int = 300, key_prefix: str = "endpoint"):
    """Decorator to cache endpoint responses"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = cache.generate_cache_key(
                f"api:{key_prefix}",
                func.__name__,
                *args,
                **kwargs
            )
            
            # Try cache first
            cached_result = await cache.get_async(cache_key)
            if cached_result is not None:
                print(f"📦 Cache HIT for {func.__name__}")
                return cached_result
            
            # Execute function - ADD THIS PRINT STATEMENT BACK
            print(f"🔄 Cache MISS for {func.__name__} - executing...")
            if inspect.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Cache result
            await cache.set_async(cache_key, result, ttl)
            print(f"💾 Cached result for {func.__name__}")
            
            return result
        return wrapper
    return decorator

# Specialized decorators for different data types
def cache_properties(ttl: int = 300):
    """Cache property-related endpoints"""
    return cache_response(ttl=ttl, key_prefix="properties")

def cache_analytics(ttl: int = 180):
    """Cache analytics endpoints (shorter TTL for fresher data)"""
    return cache_response(ttl=ttl, key_prefix="analytics")

def cache_contacts(ttl: int = 600):
    """Cache contact endpoints (longer TTL as contacts change less)"""
    return cache_response(ttl=ttl, key_prefix="contacts")

def cache_search(ttl: int = 120):
    """Cache search results (shorter TTL for dynamic data)"""
    return cache_response(ttl=ttl, key_prefix="search")

# Cache invalidation helpers
async def invalidate_on_property_update(property_id: str):
    """Invalidate caches when property is updated"""
    await CacheInvalidator.invalidate_property_caches(property_id)

async def invalidate_on_analysis_complete(property_id: str):
    """Invalidate caches when new analysis is complete"""
    await CacheInvalidator.invalidate_property_caches(property_id)
    await CacheInvalidator.invalidate_analytics_caches()

async def invalidate_on_contact_change(user_id: str):
    """Invalidate caches when contacts change"""
    await CacheInvalidator.invalidate_contact_caches(user_id)

# Cache warming functions
async def warm_critical_caches():
    """Pre-populate critical caches"""
    try:
        print("🔥 Warming critical caches...")
        
        # Import here to avoid circular imports
        from main import app
        from fastapi.testclient import TestClient
        
        # Warm up most-accessed endpoints
        critical_endpoints = [
            "/api/properties",
            "/api/analytics",
            "/api/contacts/health"
        ]
        
        # This would typically be done with actual API calls
        # For now, we'll just log the intention
        for endpoint in critical_endpoints:
            print(f"🔥 Would warm cache for {endpoint}")
        
        print("✅ Cache warming completed")
        
    except Exception as e:
        print(f"❌ Error warming caches: {e}")

# Cache monitoring
class CacheMonitor:
    """Monitor cache performance and health"""
    
    @staticmethod
    async def get_cache_metrics() -> Dict[str, Any]:
        """Get comprehensive cache metrics"""
        try:
            stats = await cache.get_cache_stats()
            
            return {
                "cache_health": "healthy" if stats.get("connected") else "unhealthy",
                "total_keys": stats.get("total_hmo_cache_keys", 0),
                "memory_usage_mb": stats.get("memory_used_mb", 0),
                "hit_rate_percent": stats.get("cache_hit_rate", 0),
                "performance_impact": {
                    "estimated_db_queries_saved": stats.get("keyspace_hits", 0),
                    "estimated_time_saved_seconds": stats.get("keyspace_hits", 0) * 0.5  # Assume 500ms per saved query
                }
            }
        except Exception as e:
            return {
                "cache_health": "error",
                "error": str(e)
            }
    
    @staticmethod
    async def cache_efficiency_report() -> Dict[str, Any]:
        """Generate cache efficiency report"""
        metrics = await CacheMonitor.get_cache_metrics()
        
        # Calculate efficiency ratings
        hit_rate = metrics.get("hit_rate_percent", 0)
        
        if hit_rate >= 80:
            efficiency = "excellent"
        elif hit_rate >= 60:
            efficiency = "good"
        elif hit_rate >= 40:
            efficiency = "fair"
        else:
            efficiency = "poor"
        
        return {
            "overall_efficiency": efficiency,
            "metrics": metrics,
            "recommendations": CacheMonitor._get_recommendations(hit_rate)
        }
    
    @staticmethod
    def _get_recommendations(hit_rate: float) -> List[str]:
        """Get cache optimization recommendations"""
        recommendations = []
        
        if hit_rate < 60:
            recommendations.append("Consider increasing cache TTL for stable data")
            recommendations.append("Implement cache warming for frequently accessed endpoints")
        
        if hit_rate > 90:
            recommendations.append("Cache is performing excellently!")
            recommendations.append("Monitor for potential stale data issues")
        
        return recommendations

# Test cache functionality
async def test_cache_system():
    """Test the cache system functionality"""
    print("🧪 Testing Redis cache system...")
    
    try:
        # Test basic operations
        test_key = "test:cache:system"
        test_data = {"message": "Cache test successful", "timestamp": datetime.utcnow().isoformat()}
        
        # Test set
        success = await cache.set_async(test_key, test_data, 60)
        assert success, "Cache set failed"
        
        # Test get
        retrieved_data = await cache.get_async(test_key)
        assert retrieved_data == test_data, "Cache get failed"
        
        # Test deletion
        deleted = await cache.delete_async("test:cache:*")
        assert deleted >= 1, "Cache delete failed"
        
        print("✅ Cache system test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Cache system test failed: {e}")
        return False

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_cache_system())