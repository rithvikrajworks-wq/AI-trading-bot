# src/api/endpoints/top_opportunities.py
import asyncio
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.services.stock_service import StockService
from app.schemas.analysis import StockAnalysisResponse, BatchAnalysisResponse, BatchErrorDetail

router = APIRouter()

@router.get("/top-opportunities", response_model=List[StockAnalysisResponse])
async def get_top_opportunities() -> List[Dict[str, Any]]:
    """Scan configured universal stock lists and return high‑confidence setups.
    The scanner respects concurrency limits and confidence thresholds defined
    in :pydata:`app.core.config.settings`.
    """
    # Assemble the ticker universe
    all_tickers: List[str] = []
    for market_list in settings.UNIVERSAL_STOCKS.values():
        all_tickers.extend(market_list)
    # Deduplicate while preserving order
    seen = set()
    tickers = []
    for t in all_tickers:
        if t not in seen:
            seen.add(t)
            tickers.append(t)
    # Cap to maximum allowed per scan
    tickers = tickers[: settings.MAX_SCAN_STOCKS]

    semaphore = asyncio.Semaphore(settings.SCAN_CONCURRENCY_LIMIT)
    stock_service = StockService()

    async def safe_analyze(ticker: str) -> Any:
        async with semaphore:
            try:
                result = await stock_service.analyze_ticker(ticker)
                return result
            except Exception as exc:
                return BatchErrorDetail(ticker=ticker, error=str(exc))

    # Run analyses concurrently, capturing both successes and errors
    raw_results = await asyncio.gather(*[safe_analyze(t) for t in tickers], return_exceptions=False)

    # Separate successes from errors
    successes: List[Dict[str, Any]] = []
    errors: List[BatchErrorDetail] = []
    for res in raw_results:
        if isinstance(res, BatchErrorDetail):
            errors.append(res)
        else:
            successes.append(res)

    # Filter high‑quality setups based on confidence threshold and risk/reward ratio
    high_quality = [s for s in successes if s.get("confidence", 0) >= settings.MIN_CONFIDENCE_THRESHOLD and s.get("risk_reward_ratio", 0) >= getattr(settings, "RISK_REWARD_THRESHOLD", 1.5)]

    # Sort by confidence descending (strongest signal first)
    high_quality.sort(key=lambda x: x.get("confidence", 0), reverse=True)

    # If no high‑quality setups found, we can optionally raise a 404 or return empty list
    if not high_quality:
        # Returning empty list keeps the API simple; clients can handle it.
        return []

    return high_quality
