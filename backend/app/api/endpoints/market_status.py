# src/api/endpoints/market_status.py
"""Market status endpoint for live UI strip.
Provides open/closed status for major exchanges and local time.
Currently returns static placeholder data; can be extended later.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone

router = APIRouter()

@router.get("/market-status")
async def get_market_status():
    """Return market open/close status and timestamps.
    In a real deployment this would query exchange calendars.
    """
    try:
        now = datetime.now(timezone.utc)
        # Placeholder logic – assume markets are open during typical hours UTC
        def is_open() -> bool:
            hour = now.hour
            return 13 <= hour <= 22  # Approx 9am-6pm EST (NY)
        status = "Open" if is_open() else "Closed"
        # Use same status for all exchanges as placeholder
        return {
            "nse": status,
            "nyse": status,
            "nasdaq": status,
            "local_time": now.isoformat(),
            "next_change_in_seconds": 3600,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
