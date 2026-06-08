# backend/app/services/usage_analytics.py

"""Analytics service for recording AI usage.
All operations are async and respect DB timeout.
"""

import datetime
import logging
from typing import Optional

import aiosqlite

from app.settings import settings
from app.utils.async_timeout import with_timeout

logger = logging.getLogger("usage_analytics")

class UsageAnalytics:
    def __init__(self):
        # Ensure DB file exists; creation handled elsewhere in app startup.
        self.db_path = settings.MEMORY_DB_PATH  # reuse memory DB path (same SQLite file)

    async def _execute(self, query: str, params: tuple = (), fetch: bool = False) -> Optional[list]:
        async def _inner():
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("PRAGMA journal_mode=WAL;")
                async with db.execute(query, params) as cursor:
                    if fetch:
                        rows = await cursor.fetchall()
                        return rows
                await db.commit()
        return await with_timeout(_inner(), settings.DB_TIMEOUT)

    async def record(
        self,
        user_id: str,
        endpoint: str,
        provider: str,
        tokens: int,
        latency: float,
        success: int,
    ) -> None:
        """Insert a usage record into `ai_usage` table.
        Table schema (already created):
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        endpoint TEXT,
        provider TEXT,
        tokens INTEGER,
        latency REAL,
        success INTEGER,
        ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """
        query = """
        INSERT INTO ai_usage (user_id, endpoint, provider, tokens, latency, success)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        try:
            await self._execute(query, (user_id, endpoint, provider, tokens, latency, success))
        except Exception as exc:
            logger.warning("Failed to record analytics for %s: %s", user_id, exc)

    async def count_user_requests(
        self, user_id: str, start_date: datetime.date, end_date: datetime.date
    ) -> int:
        """Count usage rows for a user between dates (inclusive)."""
        query = """
        SELECT COUNT(*) FROM ai_usage
        WHERE user_id = ? AND DATE(ts) BETWEEN ? AND ?
        """
        rows = await self._execute(query, (user_id, start_date.isoformat(), end_date.isoformat()), fetch=True)
        if rows:
            return rows[0][0]
        return 0

# Export singleton for easy import
usage_analytics = UsageAnalytics()
