# backend/app/api/endpoints/live_price.py
"""Live price endpoint.
Provides the latest price, delta and percent change for a ticker.
Uses a short‑lived cache (default 10 s) to avoid hammering Yahoo Finance.
"""

from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.utils.cache import cache
import yfinance as yf
from datetime import datetime, timezone

router = APIRouter()

@router.get("/live-price/{ticker}", tags=["Live Price"])  # noqa: E401
async def get_live_price(ticker: str):
    """Return live price information for *ticker*.

    Response format:
    ```json
    {
        "ticker": "AAPL",
        "price": 214.32,
        "change": 1.24,
        "change_percent": 0.58,
        "timestamp": "2026-05-27T10:00:00Z"
    }
    ```
    """
    ticker_clean = ticker.strip().upper()
    cache_key = ("live_price", ticker_clean)

    async def compute():
        try:
            yf_ticker = yf.Ticker(ticker_clean)
            # Get two days of daily data to compute change
            hist = yf_ticker.history(period="2d", interval="1d")
            if hist.empty or len(hist) < 2:
                raise ValueError("Insufficient data")
            latest = hist.iloc[-1]
            previous = hist.iloc[-2]
            price = float(latest["Close"])
            prev_price = float(previous["Close"])
            change = round(price - prev_price, 4)
            change_percent = round((change / prev_price) * 100, 2) if prev_price != 0 else 0.0
            timestamp = datetime.now(timezone.utc).isoformat()
            return {
                "ticker": ticker_clean,
                "price": round(price, 2),
                "change": change,
                "change_percent": change_percent,
                "timestamp": timestamp,
            }
        except Exception as exc:
            raise HTTPException(status_code=404, detail=str(exc))

    # Cache for 10 seconds (configurable via settings)
    ttl = getattr(settings, "LIVE_PRICE_TTL_SECONDS", 10)
    return await cache.get_or_compute(cache_key, ttl, compute, cache_name="live_price")
