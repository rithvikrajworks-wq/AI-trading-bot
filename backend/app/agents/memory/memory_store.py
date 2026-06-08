# backend/app/agents/memory/memory_store.py

"""Async SQLite memory store for episodic memories and summaries.
All operations are wrapped with `with_timeout` using the DB timeout from settings.
"""

import logging
import uuid
import time
from typing import List, Tuple, Dict, Any

import aiosqlite

from app.settings import settings
from app.utils.async_timeout import with_timeout

logger = logging.getLogger("memory_store")

class MemoryStore:
    def __init__(self):
        self.db_path = settings.MEMORY_DB_PATH

    async def _execute(self, query: str, params: tuple = (), fetch: bool = False) -> Any:
        async def _inner():
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA journal_mode=WAL;")
                async with db.execute(query, params) as cursor:
                    if fetch:
                        rows = await cursor.fetchall()
                        return rows
                await db.commit()
        return await with_timeout(_inner(), settings.DB_TIMEOUT)

    async def add_entry(self, user_id: str, role: str, content: str, importance: int) -> None:
        """Insert a new episodic memory row.
        `importance` is an integer (higher = more important).
        """
        ts = time.time()
        entry_id = str(uuid.uuid4())
        query = """
        INSERT INTO episodic_memory (id, user_id, role, content, timestamp, metadata, embedding)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        # metadata & embedding can be null now; they will be updated later by vector store.
        await self._execute(query, (entry_id, user_id, role, content, ts, None, None))
        # After insertion, enforce size limits.
        await self.prune(user_id)

    async def get_recent(self, user_id: str, limit: int = None) -> List[Tuple[str, str, str, float]]:
        """Return recent rows for *user_id* ordered by timestamp desc.
        Returns list of (role, content, timestamp, importance) tuples.
        """
        limit = limit or settings.CHAT_MEMORY_LIMIT
        query = """
        SELECT role, content, timestamp, metadata FROM episodic_memory
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        """
        rows = await self._execute(query, (user_id, limit), fetch=True)
        return rows

    async def add_summary(self, user_id: str, summary: str) -> None:
        """Insert a summary entry for *user_id* and prune if needed."""
        ts = time.time()
        summary_id = str(uuid.uuid4())
        query = """
        INSERT INTO memory_summaries (id, user_id, summary, created_at)
        VALUES (?, ?, ?, ?)
        """
        await self._execute(query, (summary_id, user_id, summary, ts))
        await self.prune_summaries(user_id)

    async def prune(self, user_id: str) -> None:
        """Enforce `MAX_MEMORY_ENTRIES_PER_USER`.
        Deletes oldest low‑importance rows first.
        """
        max_entries = settings.MAX_MEMORY_ENTRIES_PER_USER
        # Count current rows
        count_query = "SELECT COUNT(*) FROM episodic_memory WHERE user_id = ?"
        rows = await self._execute(count_query, (user_id,), fetch=True)
        current = rows[0][0] if rows else 0
        if current <= max_entries:
            return
        # Delete oldest rows until under limit. Prefer rows with low importance.
        delete_query = """
        DELETE FROM episodic_memory
        WHERE id IN (
            SELECT id FROM episodic_memory
            WHERE user_id = ?
            ORDER BY timestamp ASC
            LIMIT ?
        )
        """
        excess = current - max_entries
        await self._execute(delete_query, (user_id, excess))
        logger.info("Pruned %s episodic memory rows for user %s", excess, user_id)

    async def prune_summaries(self, user_id: str) -> None:
        """Enforce `MAX_SUMMARY_COUNT_PER_USER`."""
        max_summaries = settings.MAX_SUMMARY_COUNT_PER_USER
        count_q = "SELECT COUNT(*) FROM memory_summaries WHERE user_id = ?"
        rows = await self._execute(count_q, (user_id,), fetch=True)
        current = rows[0][0] if rows else 0
        if current <= max_summaries:
            return
        excess = current - max_summaries
        del_q = """
        DELETE FROM memory_summaries
        WHERE id IN (
            SELECT id FROM memory_summaries
            WHERE user_id = ?
            ORDER BY created_at ASC
            LIMIT ?
        )
        """
        await self._execute(del_q, (user_id, excess))
        logger.info("Pruned %s summary rows for user %s", excess, user_id)

# Export singleton
memory_store = MemoryStore()
