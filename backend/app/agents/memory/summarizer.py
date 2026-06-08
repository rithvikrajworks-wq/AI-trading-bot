# backend/app/agents/memory/summarizer.py

"""Summarizer component for condensing older conversation turns.
It creates a concise summary using the orchestrator's LLM.
"""

import logging
from typing import List, Dict, Any

from app.services.ai_orchestrator import ai_orchestrator
from app.settings import settings
from app.utils.async_timeout import with_timeout

logger = logging.getLogger("memory_summarizer")

async def summarize_history(user_id: str, messages: List[Dict[str, Any]]) -> str:
    """Summarize a list of past messages.
    *messages* is a list of dicts with keys `role` and `content`.
    Returns the summary string.
    """
    # Build a concise prompt for summarization
    prompt = (
        "You are a concise summarizer for a financial chat history. Summarize the essential "
        "trading preferences, strategies, risk tolerance, favorite tickers, and any other "
        "relevant user intents. Keep the summary under 200 words."
        "\n\nChat history:\n"
    )
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        prompt += f"{role.title()}: {content}\n"
    prompt += "\nSummary:" 
    try:
        # Use orchestrator generate with a short timeout
        summary = await with_timeout(
            ai_orchestrator.generate(user_id, prompt, endpoint="summarize"),
            settings.PROVIDER_TIMEOUT,
        )
        logger.debug("Generated summary for user %s", user_id)
        return summary
    except Exception as exc:
        logger.warning("Summarization failed for user %s: %s", user_id, exc)
        raise
