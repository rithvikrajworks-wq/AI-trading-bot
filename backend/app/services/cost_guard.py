# backend/app/services/cost_guard.py

"""Cost protection utilities.
Enforces per‑user request and token quotas.
Raises ``fastapi.HTTPException`` (429) when limits are exceeded.
"""

import datetime
import asyncio
from fastapi import HTTPException, status

from app.settings import settings
from app.utils.async_timeout import with_timeout
from app.services.usage_analytics import UsageAnalytics

# Re‑use the singleton analytics for quick token counting
analytics = UsageAnalytics()

async def verify_cost_limits(user_id: str, token_count: int) -> None:
    """Validate that a user may make a request of *token_count* tokens.

    Checks daily and monthly request counters as well as a maximum
    cumulative token budget (``MAX_CONTEXT_TOKENS``).  If any check fails,
    raises ``HTTPException(status_code=429)`` with a descriptive message.
    """
    # Apply DB timeout wrapper
    async def _query_counts():
        now = datetime.datetime.utcnow()
        today = now.date()
        month_start = now.replace(day=1).date()
        # Count rows from ai_usage table (must exist) – we use analytics helper
        daily = await analytics.count_user_requests(user_id, start_date=today, end_date=today)
        monthly = await analytics.count_user_requests(user_id, start_date=month_start, end_date=today)
        return daily, monthly

    daily, monthly = await with_timeout(_query_counts(), settings.DB_TIMEOUT)

    if daily >= settings.MAX_DAILY_AI_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Daily AI request limit exceeded.",
        )
    if monthly >= settings.MAX_MONTHLY_AI_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Monthly AI request limit exceeded.",
        )
    # Simple token budget per request – can be extended to cumulative token tracking
    if token_count > settings.MAX_CONTEXT_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Prompt exceeds maximum allowed tokens ({settings.MAX_CONTEXT_TOKENS}).",
        )
