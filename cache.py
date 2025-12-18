# ============================================================================
# FILE: src/cache.py
# ============================================================================
"""Caching layer with TTL support"""
import time
import json
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod


class CacheBackend(ABC):
    """Abstract cache backend"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 300):
        pass
    
    @abstractmethod
    async def delete(self, key: str):
        pass
    
    @abstractmethod
    async def clear(self):
        pass


class InMemoryCache(CacheBackend):
    """In-memory cache with TTL (use Redis in production)"""
    
    def __init__(self):
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._stats = {"hits": 0, "misses": 0}
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                self._stats["hits"] += 1
                return value
            else:
                del self._cache[key]
        self._stats["misses"] += 1
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL"""
        expiry = time.time() + ttl
        self._cache[key] = (value, expiry)
    
    async def delete(self, key: str):
        """Delete key from cache"""
        self._cache.pop(key, None)
    
    async def clear(self):
        """Clear all cache"""
        self._cache.clear()
        self._stats = {"hits": 0, "misses": 0}
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0
        return {
            **self._stats,
            "total_requests": total,
            "hit_rate": round(hit_rate, 3)
        }
