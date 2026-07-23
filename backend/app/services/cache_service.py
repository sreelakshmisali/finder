"""
Search Cache Service

Provides in-memory caching for job search queries with TTL expiration, user-level invalidation,
and in-flight request deduplication/coalescing to prevent expensive duplicate ATS API calls.
"""

import asyncio
import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def make_cache_key(
    user_id: Optional[uuid.UUID],
    query: Optional[str],
    location: Optional[str],
    remote_only: bool,
    providers: Optional[List[str]],
    min_salary: Optional[int],
    limit: int
) -> str:
    """
    Generates a canonical cache key based on final applied search parameters.
    """
    user_str = str(user_id) if user_id else "anon"
    q_str = (query or "").strip().lower()
    loc_str = (location or "").strip().lower()
    remote_str = "remote" if remote_only else "all"
    prov_str = "_".join(sorted([p.lower() for p in providers])) if providers else "all_providers"
    sal_str = str(min_salary) if min_salary else "any_sal"
    limit_str = str(limit)

    return f"search:{user_str}:{q_str}:{loc_str}:{remote_str}:{prov_str}:{sal_str}:{limit_str}"


class SearchCache:
    """
    Async-safe in-memory cache manager for job search results.
    """

    def __init__(self, default_ttl_seconds: int = 1200):  # 20 minutes
        self.default_ttl = default_ttl_seconds
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._in_flight: Dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieves cached payload if key exists and has not expired.
        """
        async with self._global_lock:
            if key not in self._cache:
                return None

            value, expire_at = self._cache[key]
            if time.time() >= expire_at:
                logger.debug(f"Cache key expired: {key}")
                del self._cache[key]
                return None

            return value

    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Stores payload in cache with specified TTL.
        """
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        expire_at = time.time() + ttl
        async with self._global_lock:
            self._cache[key] = (value, expire_at)
            logger.debug(f"Cached search result for key '{key}' (TTL={ttl}s)")

    async def get_key_lock(self, key: str) -> asyncio.Lock:
        """
        Returns a per-key lock used for in-flight request coalescing.
        """
        async with self._global_lock:
            if key not in self._in_flight:
                self._in_flight[key] = asyncio.Lock()
            return self._in_flight[key]

    async def cleanup_key_lock(self, key: str) -> None:
        """
        Cleans up in-flight lock after execution completes.
        """
        async with self._global_lock:
            lock = self._in_flight.get(key)
            if lock and not lock.locked():
                del self._in_flight[key]

    async def invalidate_user(self, user_id: uuid.UUID) -> int:
        """
        Invalidates all cached search results associated with a specific user.
        Called when user profile, preferences, or active resume change.
        """
        prefix = f"search:{str(user_id)}:"
        count = 0
        async with self._global_lock:
            keys_to_del = [k for k in self._cache.keys() if k.startswith(prefix)]
            for k in keys_to_del:
                del self._cache[k]
                count += 1

        if count > 0:
            logger.info(f"Invalidated {count} search cache entries for user {user_id}")
        return count

    async def clear(self) -> None:
        """
        Clears all cached entries.
        """
        async with self._global_lock:
            self._cache.clear()
            self._in_flight.clear()
            logger.info("Search cache completely cleared.")


# Singleton search cache instance
search_cache = SearchCache(default_ttl_seconds=1200)
