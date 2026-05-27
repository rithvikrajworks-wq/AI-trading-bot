import asyncio
import time
from typing import Any, Callable, Coroutine, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class CacheEntry:
    def __init__(self, value: Any, expires_at: float):
        self.value = value
        self.expires_at = expires_at

class InMemoryCache:
    """Simple TTL‑based in‑memory cache with async‑safe in‑flight deduplication.
    Designed to be a drop‑in replacement for a Redis‑backed implementation.
    """
    def __init__(self):
        self._store: Dict[Tuple, CacheEntry] = {}
        self._locks: Dict[Tuple, asyncio.Event] = {}
        self._global_lock = asyncio.Lock()

    async def get(self, key: Tuple) -> Any | None:
        entry = self._store.get(key)
        if entry and entry.expires_at > time.time():
            return entry.value
        # expired – clean up
        if key in self._store:
            del self._store[key]
        return None

    async def set(self, key: Tuple, value: Any, ttl: int):
        async with self._global_lock:
            self._store[key] = CacheEntry(value, time.time() + ttl)

    async def get_or_compute(
        self,
        key: Tuple,
        ttl: int,
        compute_fn: Callable[[], Coroutine[Any, Any, Any]],
        cache_name: str = "cache",
    ) -> Any:
        """Return cached value or compute it.
        Handles concurrent calls for the same key by allowing only the first
        coroutine to run ``compute_fn``; the rest wait for the ``Event``.
        """
        # Fast path – check cache
        cached = await self.get(key)
        if cached is not None:
            logger.debug(f"[CACHE HIT] {cache_name} key={key}")
            return cached
        logger.debug(f"[CACHE MISS] {cache_name} key={key}")

        # Deduplication handling
        async with self._global_lock:
            if key not in self._locks:
                # First request creates an Event for others to wait on
                self._locks[key] = asyncio.Event()
                is_leader = True
            else:
                is_leader = False
                wait_event = self._locks[key]

        if is_leader:
            try:
                result = await compute_fn()
                await self.set(key, result, ttl)
                return result
            finally:
                async with self._global_lock:
                    # Wake up waiting coroutines
                    self._locks[key].set()
                    del self._locks[key]
        else:
            # Wait for leader to finish computation
            await wait_event.wait()
            # Result should now be cached
            return await self.get(key)

# Module‑level singleton for process‑wide usage
cache = InMemoryCache()
