# backend/app/agents/memory_agent.py

"""High‑level memory agent.
Provides `store_message` and `retrieve_relevant` APIs used by the ChatAgent.
Implements importance scoring, prompt‑injection filtering, and vector store interaction.
"""

import logging
import re
from typing import List, Dict, Any

from app.settings import settings
from app.agents.memory.memory_store import memory_store
from app.agents.memory.vector_store import vector_store
from app.agents.memory.embeddings import embed_text

logger = logging.getLogger("memory_agent")

# Simple list of disallowed prompt injection phrases (lower‑cased for matching)
DISALLOWED_PHRASES = [
    r"ignore previous instructions",
    r"reveal system prompt",
    r"disable safety",
]
DISALLOWED_REGEX = re.compile("|".join(DISALLOWED_PHRASES), re.IGNORECASE)

def _score_importance(content: str) -> int:
    """Return an integer importance score.
    High importance (10) for key user intents; low (1) otherwise.
    """
    keywords = ["preference", "strategy", "risk", "tolerance", "favorite ticker", "goal", "risk tolerance", "trading style"]
    lower = content.lower()
    for kw in keywords:
        if kw in lower:
            return 10
    # Long messages may still be valuable
    if len(content) > 200:
        return 5
    return 1

def _filter_injection(text: str) -> str:
    """Remove disallowed injection phrases from *text*.
    Returns the cleaned text.
    """
    return DISALLOWED_REGEX.sub("", text)

class MemoryAgent:
    async def store_message(self, user_id: str, role: str, content: str) -> None:
        """Store a message with importance scoring and optional vector indexing.
        *role* is typically "user" or "assistant".
        """
        clean_content = _filter_injection(content)
        importance = _score_importance(clean_content)
        await memory_store.add_entry(user_id, role, clean_content, importance)
        # Only embed high‑importance entries to keep vector store size manageable
        if importance >= 5:
            try:
                embedding = await embed_text(user_id, clean_content)
                await vector_store.add_vector(user_id, embedding, {"role": role, "content": clean_content})
            except Exception as exc:
                logger.warning("Failed to embed/store vector for user %s: %s", user_id, exc)

    async def retrieve_relevant(self, user_id: str, query: str) -> List[Dict[str, Any]]:
        """Retrieve up to `MAX_SEMANTIC_RETRIEVAL` relevant memories for *query*.
        Returns list of metadata dicts (role, content).
        """
        try:
            query_vec = await embed_text(user_id, query)
            results = await vector_store.search(query_vec)
            # Filter only entries that belong to this user (vector store may contain others)
            filtered = [r["metadata"] for r in results if r.get("user_id") == user_id]
            return filtered
        except Exception as exc:
            logger.warning("Memory retrieval failed for user %s: %s", user_id, exc)
            return []

    # ---------------------------------------------------------------------
    # Analysis context helpers
    # ---------------------------------------------------------------------
    async def get_latest_analysis_context(self, ticker: str) -> str:
        """Return a short formatted string for the most recent analysis of *ticker*.
        Includes date, signal, confidence and a truncated summary.
        """
        from ..repositories.analysis_repo import get_latest_analysis
        from ..database import SessionLocal
        try:
            db = SessionLocal()
            record = get_latest_analysis(db, ticker)
            if not record:
                return ""
            summary = record.analysis_text
            if len(summary) > 200:
                summary = summary[:200] + "..."
            ctx = (
                f"Latest Analysis for {ticker.upper()}:\n"
                f"Date: {record.created_at.date()}\n"
                f"Signal: {record.signal}\n"
                f"Confidence: {record.confidence}%\n"
                f"Summary: {summary}\n"
            )
            logger.info(
                "analysis_history_loaded",
                extra={"ticker": ticker, "records_found": 1, "context_length": len(ctx)},
            )
            return ctx
        except Exception as exc:
            logger.warning("Failed to load latest analysis for %s: %s", ticker, exc)
            return ""
        finally:
            db.close()

    async def get_recent_analysis_context(self, ticker: str, limit: int = 5) -> str:
        """Return a formatted block with up to *limit* recent analyses for *ticker*.
        The latest analysis is always included; older entries are truncated to keep prompt size reasonable.
        """
        from ..repositories.analysis_repo import get_recent_analyses
        from ..database import SessionLocal
        try:
            db = SessionLocal()
            records = get_recent_analyses(db, ticker, limit=limit)
            if not records:
                return ""
            parts = [f"Previous Analysis History for {ticker.upper()}:\n"]
            for rec in records:
                summary = rec.analysis_text
                if len(summary) > 150:
                    summary = summary[:150] + "..."
                parts.append(
                    f"{rec.created_at.date()}\n"
                    f"Signal: {rec.signal}\n"
                    f"Confidence: {rec.confidence}%\n"
                    f"Summary: {summary}\n"
                )
            ctx = "\n".join(parts)
            logger.info(
                "analysis_context_created",
                extra={"ticker": ticker, "records_found": len(records), "context_length": len(ctx)},
            )
            return ctx
        except Exception as exc:
            logger.warning("Failed to load recent analyses for %s: %s", ticker, exc)
            return ""
        finally:
            db.close()

    async def get_analysis_context(self, ticker: str) -> str:
        """Convenient wrapper returning the recent analysis block (includes latest)."""
        return await self.get_recent_analysis_context(ticker)

# Export singleton
memory_agent = MemoryAgent()
