"""
Cache Layer - Optional Redis with NullCache Fallback
Safe serialization and configurable TTL
"""

from typing import Optional, Any
import json
from config.settings import settings


class NullCache:
    """
    Null object pattern for cache
    Used when Redis is disabled
    """
    def get(self, key: str) -> Optional[str]:
        return None
    
    def set(self, key: str, value: str, ex: Optional[int] = None):
        return True
    
    def delete(self, key: str):
        return True
    
    def exists(self, key: str):
        return False


def _serializer(obj: Any) -> str:
    """Safe JSON serialization"""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def _deserializer(s: str) -> Any:
    """Safe JSON deserialization"""
    try:
        return json.loads(s)
    except (json.JSONDecodeError, TypeError):
        return None


# Initialize cache based on configuration
if settings.REDIS_ENABLED:
    try:
        from redis import Redis
        redis = Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1
        )
        # Test connection
        redis.ping()
        print(f"✅ Redis cache enabled: {settings.REDIS_URL}")
    except Exception as e:
        print(f"⚠️ Redis connection failed, using NullCache: {e}")
        redis = NullCache()
else:
    redis = NullCache()
    print("ℹ️ Redis cache disabled, using NullCache")


def cache_get(key: str) -> Optional[Any]:
    """
    Get value from cache
    Returns deserialized object or None
    """
    try:
        value = redis.get(key)
        if value is None:
            return None
        
        # Handle bytes (if decode_responses=False)
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        
        return _deserializer(value)
    except Exception as e:
        print(f"⚠️ Cache get error for key {key}: {e}")
        return None


def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """
    Set value in cache
    Serializes object and applies TTL
    """
    try:
        ttl = ttl or settings.CACHE_DEFAULT_TTL_S
        serialized = _serializer(value)
        return redis.set(key, serialized, ex=ttl)
    except Exception as e:
        print(f"⚠️ Cache set error for key {key}: {e}")
        return False


def cache_delete(key: str) -> bool:
    """Delete key from cache"""
    try:
        return redis.delete(key) > 0
    except Exception as e:
        print(f"⚠️ Cache delete error for key {key}: {e}")
        return False


def cache_exists(key: str) -> bool:
    """Check if key exists in cache"""
    try:
        return redis.exists(key) > 0
    except Exception as e:
        return False


# Cache statistics (for monitoring)
def get_cache_stats() -> dict:
    """Get cache statistics for monitoring"""
    if isinstance(redis, NullCache):
        return {
            "enabled": False,
            "type": "NullCache"
        }
    
    try:
        info = redis.info("stats")
        return {
            "enabled": True,
            "type": "Redis",
            "hits": info.get("keyspace_hits", 0),
            "misses": info.get("keyspace_misses", 0),
            "hit_ratio": info.get("keyspace_hits", 0) / max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1), 1)
        }
    except Exception as e:
        return {
            "enabled": True,
            "type": "Redis",
            "error": str(e)
        }
