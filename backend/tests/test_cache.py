"""
Unit tests for SearchCache service using standard python assertions.
"""

import asyncio
import time
import uuid
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.cache_service import SearchCache, make_cache_key


async def test_make_cache_key():
    user_id = uuid.uuid4()
    key1 = make_cache_key(user_id, "Python", "San Francisco", True, ["greenhouse"], 100000, 50)
    key2 = make_cache_key(user_id, "python ", " San Francisco ", True, ["GREENHOUSE"], 100000, 50)
    assert key1 == key2, "Cache key generation should be normalized and case-insensitive"

    key3 = make_cache_key(user_id, "Java", "San Francisco", True, ["greenhouse"], 100000, 50)
    assert key1 != key3, "Different queries should produce different cache keys"
    print("test_make_cache_key: PASSED")


async def test_cache_set_and_get():
    cache = SearchCache(default_ttl_seconds=2)
    key = "test_key_1"
    data = {"jobs": ["job1", "job2"], "total": 2}

    await cache.set(key, data)
    retrieved = await cache.get(key)
    assert retrieved == data, "Retrieved cache data should match stored payload"
    print("test_cache_set_and_get: PASSED")


async def test_cache_expiration():
    cache = SearchCache(default_ttl_seconds=1)
    key = "expiring_key"
    data = {"test": 123}

    await cache.set(key, data, ttl_seconds=1)
    assert await cache.get(key) == data, "Should hit cache before expiration"

    await asyncio.sleep(1.1)
    assert await cache.get(key) is None, "Should miss cache after expiration"
    print("test_cache_expiration: PASSED")


async def test_invalidate_user():
    cache = SearchCache(default_ttl_seconds=300)
    user_id = uuid.uuid4()
    other_user_id = uuid.uuid4()

    key1 = make_cache_key(user_id, "Python", None, False, None, None, 50)
    key2 = make_cache_key(user_id, "React", None, False, None, None, 50)
    key3 = make_cache_key(other_user_id, "Python", None, False, None, None, 50)

    await cache.set(key1, "user1_data1")
    await cache.set(key2, "user1_data2")
    await cache.set(key3, "user2_data")

    count = await cache.invalidate_user(user_id)
    assert count == 2, "Should invalidate exactly 2 entries for user1"

    assert await cache.get(key1) is None
    assert await cache.get(key2) is None
    assert await cache.get(key3) == "user2_data", "Other user cache entries must remain intact"
    print("test_invalidate_user: PASSED")


async def run_all():
    await test_make_cache_key()
    await test_cache_set_and_get()
    await test_cache_expiration()
    await test_invalidate_user()
    print("\nAll SearchCache unit tests PASSED successfully!")


if __name__ == "__main__":
    asyncio.run(run_all())
