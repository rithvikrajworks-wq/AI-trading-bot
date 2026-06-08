# backend/app/services/ai_orchestrator.py

"""Lightweight orchestrator that coordinates AI calls.
It delegates to ProviderFactory, applies retries, cost guard, analytics, and response guard.
All heavy logic (memory, validation) stays in dedicated modules.
"""

import logging
import time
from typing import Any, Dict

from app.settings import settings
from .provider_factory import provider_factory
from .cost_guard import verify_cost_limits
from .response_guard import ResponseGuard
from .usage_analytics import UsageAnalytics

logger = logging.getLogger("ai_orchestrator")

class AIOrchestrator:
    def __init__(self):
        self.response_guard = ResponseGuard()
        self.analytics = UsageAnalytics()
        # Simple exponential backoff params
        self.max_retries = 3
        self.backoff_factor = 2  # seconds

    async def _run_with_retries(self, func, *args, **kwargs):
        """Execute async func with exponential backoff retries.
        Returns the result of the first successful call.
        """
        attempt = 0
        while attempt < self.max_retries:
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                attempt += 1
                logger.warning(
                    "Attempt %s/%s failed for %s: %s",
                    attempt,
                    self.max_retries,
                    func.__name__,
                    exc,
                )
                if attempt >= self.max_retries:
                    raise
                await asyncio.sleep(self.backoff_factor ** attempt)

    async def generate(self, user_id: str, prompt: str, endpoint: str = "generic") -> str:
        """High‑level generation workflow.
        - Cost guard check.
        - Provider generation via ProviderFactory.
        - Response guard (JSON repair, sanity checks, disclaimer).
        - Analytics logging.
        """
        # Cost guard (may raise HTTPException)
        await verify_cost_limits(user_id, len(prompt))
        start = time.time()
        # Provider generation with internal retries (the orchestrator also retries on failure)
        raw_response = await self._run_with_retries(provider_factory.generate, prompt)
        # Apply response guard (e.g., JSON repair, numeric clamps, disclaimer)
        guarded = await self.response_guard.guard(raw_response, context={"user_id": user_id})
        latency = time.time() - start
        # Record analytics if enabled
        if settings.ENABLE_ANALYTICS:
            await self.analytics.record(
                user_id=user_id,
                endpoint=endpoint,
                provider="gemini" if provider_factory.primary else "fallback",
                tokens=self._estimate_tokens(prompt + guarded),
                latency=latency,
                success=1,
            )
        return guarded

    async def embed(self, user_id: str, text: str) -> Any:
        """Embedding workflow with cost guard and analytics.
        """
        await verify_cost_limits(user_id, len(text))
        start = time.time()
        embedding = await self._run_with_retries(provider_factory.embed, text)
        latency = time.time() - start
        if settings.ENABLE_ANALYTICS:
            await self.analytics.record(
                user_id=user_id,
                endpoint="embed",
                provider="gemini" if provider_factory.primary else "fallback",
                tokens=self._estimate_tokens(text),
                latency=latency,
                success=1,
            )
        return embedding

    def _estimate_tokens(self, text: str) -> int:
        # Rough estimation: 1 token ≈ 1.5 characters (average)
        return max(1, int(len(text) / 1.5))

# Export a singleton for easy import throughout the codebase
ai_orchestrator = AIOrchestrator()
