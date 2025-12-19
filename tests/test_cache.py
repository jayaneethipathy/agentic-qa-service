# ============================================================================
# FILE: tests/test_cache.py
# ============================================================================
"""Tests for caching layer"""
import pytest
import asyncio
from src.cache import InMemoryCache


@pytest.mark.asyncio
async def test_cache_set_and_get():
    """Test basic cache set and get"""
    cache = InMemoryCache()
    
    await cache.set("test_key", "test_value", ttl=10)
    result = await cache.get("test_key")
    
    assert result == "test_value"
    await cache.clear()


@pytest.mark.asyncio
async def test_cache_expiry():
    """Test cache TTL expiration"""
    cache = InMemoryCache()
    
    # Set with 1 second TTL
    await cache.set("temp_key", "temp_value", ttl=1)
    
    # Should exist immediately
    result1 = await cache.get("temp_key")
    assert result1 == "temp_value"
    
    # Wait for expiry
    await asyncio.sleep(1.1)
    
    # Should be expired
    result2 = await cache.get("temp_key")
    assert result2 is None
    
    await cache.clear()


@pytest.mark.asyncio
async def test_cache_miss():
    """Test cache miss returns None"""
    cache = InMemoryCache()
    result = await cache.get("nonexistent_key")
    assert result is None


@pytest.mark.asyncio
async def test_cache_delete():
    """Test cache deletion"""
    cache = InMemoryCache()
    
    await cache.set("delete_me", "value")
    assert await cache.get("delete_me") == "value"
    
    await cache.delete("delete_me")
    assert await cache.get("delete_me") is None


@pytest.mark.asyncio
async def test_cache_clear():
    """Test clearing entire cache"""
    cache = InMemoryCache()
    
    await cache.set("key1", "value1")
    await cache.set("key2", "value2")
    await cache.set("key3", "value3")
    
    await cache.clear()
    
    assert await cache.get("key1") is None
    assert await cache.get("key2") is None
    assert await cache.get("key3") is None


@pytest.mark.asyncio
async def test_cache_stats():
    """Test cache statistics"""
    cache = InMemoryCache()
    
    # Generate hits and misses
    await cache.set("key1", "value1")
    await cache.get("key1")  # Hit
    await cache.get("key1")  # Hit
    await cache.get("nonexistent")  # Miss
    
    stats = cache.get_stats()
    
    assert stats["hits"] == 2
    assert stats["misses"] == 1
    assert stats["total_requests"] == 3
    assert 0 <= stats["hit_rate"] <= 1
    
    await cache.clear()


@pytest.mark.asyncio
async def test_cache_overwrites():
    """Test that set overwrites existing values"""
    cache = InMemoryCache()
    
    await cache.set("key", "value1")
    await cache.set("key", "value2")
    
    result = await cache.get("key")
    assert result == "value2"
    
    await cache.clear()


@pytest.mark.asyncio
async def test_cache_complex_objects():
    """Test caching complex objects"""
    cache = InMemoryCache()
    
    complex_obj = {
        "list": [1, 2, 3],
        "nested": {"a": 1, "b": 2},
        "string": "test"
    }
    
    await cache.set("complex", complex_obj)
    result = await cache.get("complex")
    
    assert result == complex_obj
    assert isinstance(result, dict)
    
    await cache.clear()