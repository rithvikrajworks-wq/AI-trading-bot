import asyncio
import logging
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.services.stock_service import StockService
from app.schemas.ranked_opportunity_response import RankedOpportunityResponse
from app.agents.scanner_agent import ScannerAgent
from app.agents.ranking_agent import RankingAgent
from app.utils.cache import cache

logger = logging.getLogger("app.api.endpoints.top_opportunities")
router = APIRouter()

@router.get("/top-opportunities", response_model=List[RankedOpportunityResponse])
async def get_top_opportunities() -> List[Dict[str, Any]]:
    """Return AI‑generated top trading opportunities ranked by Gemini.

    Flow:
    1️⃣ Check cache (key ``scanner:top_opportunities``).
    2️⃣ If cached, return cached ``RankedOpportunityResponse`` list.
    3️⃣ Otherwise, assemble ticker universe, run ``ScannerAgent`` to get analyses.
    4️⃣ Rank using ``RankingAgent`` (Gemini).
    5️⃣ Cache the sorted results for ``settings.SCANNER_CACHE_TTL`` seconds.
    """
    cache_key = "scanner:top_opportunities"
    try:
        cached = await cache.get(cache_key)
        if cached:
            logger.info("Cache hit for top‑opportunities", extra={"cache_hit": True})
            return [RankedOpportunityResponse(**item) for item in cached]
    except Exception as e:
        logger.error("Cache retrieval error for top‑opportunities: %s", e)

    # 1️⃣ Assemble the ticker universe
    all_tickers: List[str] = []
    for market_list in settings.UNIVERSAL_STOCKS.values():
        all_tickers.extend(market_list)
    # Deduplicate while preserving order
    seen = set()
    tickers: List[str] = []
    for t in all_tickers:
        if t not in seen:
            seen.add(t)
            tickers.append(t)
    # Respect max scan limit
    tickers = tickers[: settings.MAX_SCAN_STOCKS]

    # 2️⃣ Run AI analyses concurrently via ScannerAgent
    scanner = ScannerAgent()
    try:
        analyses: List[Dict[str, Any]] = await scanner.scan(tickers)
    except Exception as e:
        logger.error("ScannerAgent failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to generate opportunities.")

    if not analyses:
        logger.warning("ScannerAgent returned no successful analyses.")
        return []

    # Filter out failed analyses
    valid_analyses = [a for a in analyses if a.get("confidence", 0) > 0]
    if not valid_analyses:
        return []

    # 3️⃣ Ranking logic - rank using Gemini via RankingAgent
    ranking_agent = RankingAgent()
    try:
        ranked_meta = await ranking_agent.rank(valid_analyses)
        analyses = ranked_meta
    except Exception as e:
        logger.error("RankingAgent failed: %s. Using default fallback order.", e)

    # 4️⃣ Cache the sorted results (list of dicts compatible with RankedOpportunityResponse)
    try:
        await cache.set(cache_key, analyses, ttl=settings.SCANNER_CACHE_TTL)
        logger.info("Cached top‑opportunities results", extra={"cache_hit": False})
    except Exception as e:
        logger.error("Failed to cache top‑opportunities: %s", e)

    # Convert to response models
    return [RankedOpportunityResponse(**a) for a in analyses]
