# backend/app/agents/memory/vector_store.py

"""Async FAISS vector store for semantic memory retrieval.
If FAISS is unavailable, falls back to an in‑memory list implementation.
All public methods respect settings.FAISS_TIMEOUT and the circuit breaker.
"""

import logging
from typing import List, Tuple, Any

from app.settings import settings
from app.utils.async_timeout import with_timeout
from app.services.circuit_breaker import circuit_breaker

logger = logging.getLogger("vector_store")

try:
    import faiss  # type: ignore
    FAISS_AVAILABLE = True
except Exception:  # pragma: no cover
    FAISS_AVAILABLE = False
    logger.warning("FAISS library not available – using in‑memory fallback for vector store.")

class VectorStore:
    def __init__(self):
        self.index_path = settings.VECTOR_DB_PATH
        if FAISS_AVAILABLE:
            # Using IndexFlatL2 for simplicity – can be swapped for IVF etc.
            self.dimension = 768  # typical embedding size; adjust if needed
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata: List[Tuple[str, dict]] = []  # (user_id, meta)
        else:
            self.vectors: List[Tuple[str, List[float], dict]] = []  # (user_id, vector, meta)

    async def add_vector(self, user_id: str, vector: List[float], metadata: dict) -> None:
        """Add a vector for *user_id* with associated *metadata*.
        Wrapped with timeout and circuit‑breaker failure handling.
        """
        if not circuit_breaker.is_healthy("faiss"):
            logger.warning("Skipping FAISS add because circuit breaker is open.")
            return
        async def _inner():
            if FAISS_AVAILABLE:
                import numpy as np
                np_vec = np.array([vector], dtype="float32")
                self.index.add(np_vec)
                self.metadata.append((user_id, metadata))
            else:
                self.vectors.append((user_id, vector, metadata))
        await with_timeout(_inner(), settings.FAISS_TIMEOUT)

    async def search(self, query_vector: List[float], k: int = None) -> List[dict]:
        """Return up to *k* nearest metadata entries for the query vector.
        If *k* is None, uses settings.MAX_SEMANTIC_RETRIEVAL.
        """
        k = k or settings.MAX_SEMANTIC_RETRIEVAL
        if not circuit_breaker.is_healthy("faiss"):
            logger.warning("FAISS search skipped due to open circuit breaker.")
            return []
        async def _inner():
            if FAISS_AVAILABLE:
                import numpy as np
                np_query = np.array([query_vector], dtype="float32")
                distances, indices = self.index.search(np_query, k)
                results = []
                for idx in indices[0]:
                    if idx < len(self.metadata):
                        user, meta = self.metadata[idx]
                        results.append({"user_id": user, "metadata": meta})
                return results
            else:
                # Simple linear search fallback
                def cosine_sim(a, b):
                    import math
                    dot = sum(x * y for x, y in zip(a, b))
                    norm_a = math.sqrt(sum(x * x for x in a))
                    norm_b = math.sqrt(sum(y * y for y in b))
                    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0
                scored = []
                for uid, vec, meta in self.vectors:
                    scored.append((cosine_sim(query_vector, vec), {"user_id": uid, "metadata": meta}))
                scored.sort(key=lambda x: x[0], reverse=True)
                return [item[1] for item in scored[:k]]
        return await with_timeout(_inner(), settings.FAISS_TIMEOUT)

# Export a singleton for easy import
vector_store = VectorStore()
