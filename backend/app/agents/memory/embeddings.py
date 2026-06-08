# backend/app/agents/memory/embeddings.py

"""Embeddings utility for the memory subsystem.
Calls the orchestrator's embed method with timeout handling.
"""

import logging
from typing import List

from app.services.ai_orchestrator import ai_orchestrator
from app.settings import settings
from app.utils.async_timeout import with_timeout

logger = logging.getLogger("memory_embeddings")

async def embed_text(user_id: str, text: str) -> List[float]:
    """Generate an embedding for *text* on behalf of *user_id*.
    The call is wrapped with the configured embedding timeout.
    """
    try:
        embedding = await with_timeout(ai_orchestrator.embed(user_id, text), settings.EMBEDDING_TIMEOUT)
        return embedding
    except Exception as exc:
        logger.warning("Embedding failed for user %s: %s", user_id, exc)
        raise
