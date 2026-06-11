import asyncio
import logging
import time
from fastapi import APIRouter, Query, HTTPException, Depends

# Response models
from app.agents.analysis_response import AnalysisResponse
from app.schemas.analysis import (
    BatchAnalysisRequest,
    BatchAnalysisResponse,
    BatchErrorDetail,
)

# Services and agents
from app.services.stock_service import StockService
from app.agents.analysis_agent import AnalysisAgent

# Utilities
from app.utils.cache import cache
from app.core.config import settings

logger = logging.getLogger("app.api.endpoints.analysis")
router = APIRouter()

@router.get(
    "/analyze-stock",
    response_model=AnalysisResponse,
    summary="Analyze Stock Ticker",
    description=(
        "Fetch raw market data via StockService, then generate an AI‑native "
        "analysis using the AnalysisAgent. The response follows the "
        "AnalysisResponse schema."
    ),
)
async def analyze_stock(
    ticker: str = Query(
        ..., min_length=1, max_length=10, description="The stock ticker symbol (e.g. NVDA, AAPL, MSFT)"
    ),
    stock_service: StockService = Depends(),
):
    """Endpoint that returns AI‑generated analysis for a single ticker.

    Steps:
    1️⃣ Retrieve raw market data via ``stock_service.get_raw_analysis_data``.
    2️⃣ Check AI analysis cache (key ``analysis:{ticker}``).
    3️⃣ If cached, return cached ``AnalysisResponse``.
    4️⃣ Otherwise invoke ``AnalysisAgent`` to produce a JSON‑structured analysis.
    5️⃣ Cache the validated response and return it.
    """
    ticker_clean = ticker.strip().upper()
    cache_key = f"analysis:{ticker_clean}"
    try:
        cached = await cache.get(cache_key)
        if cached:
            logger.info(
                "Cache hit for analysis",
                extra={"ticker": ticker_clean, "cache_hit": True},
            )
            return AnalysisResponse(**cached)
    except Exception as e:
        logger.error("Cache retrieval error for %s: %s", ticker_clean, e)

    # Fetch raw numeric data (no deterministic logic)
    try:
        raw_data = await stock_service.get_raw_analysis_data(ticker_clean)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching raw data: {e}")

    # Run AI analysis with timing and retry visibility handled inside the agent
    start_ms = int(time.time() * 1000)
    try:
        agent = AnalysisAgent()
        analysis = await agent.analyze(ticker=ticker_clean, market_data=raw_data)
    except Exception as e:
        duration_ms = int(time.time() * 1000) - start_ms
        logger.error(
            "AnalysisAgent failed for %s after %d ms: %s",
            ticker_clean,
            duration_ms,
            e,
        )
        # Fallback safe response – minimal but schema‑compatible
        fallback = AnalysisResponse(
            signal="HOLD",
            confidence=50,
            breakout_probability=50,
            risk_level="Unknown",
            summary="AI analysis unavailable – returning default hold recommendation.",
            company_overview="Data not available.",
            technical_analysis="Service unavailable.",
            chart_analysis="Data not available.",
            trend_analysis="Data not available.",
            momentum_analysis="Data not available.",
            support_resistance_analysis="Data not available.",
            bull_case="N/A",
            bear_case="N/A",
            investment_thesis="N/A",
            position_assessment="N/A",
            entry_strategy="Wait for server to recover.",
            exit_strategy="N/A",
            holding_period="N/A",
            holding_period_rationale="N/A",
            key_levels=[],
            warnings=["AI service failure – using fallback response"],
            setup_quality="low",
            market_bias="neutral",
            catalyst_summary="None",
        )
        return fallback
    finally:
        duration_ms = int(time.time() * 1000) - start_ms
        logger.info(
            "AnalysisAgent completed",
            extra={
                "ticker": ticker_clean,
                "duration_ms": duration_ms,
                "cache_hit": False,
            },
        )

    # Cache the successful response
    try:
        await cache.set(
            cache_key,
            analysis.model_dump(),
            ttl=settings.ANALYSIS_CACHE_TTL,
        )
    except Exception as e:
        logger.error("Failed to cache analysis for %s: %s", ticker_clean, e)

    return analysis

# Batch endpoint (still deterministic for now)
@router.post(
    "/analyze-stocks",
    response_model=BatchAnalysisResponse,
    summary="Batch Analyze Stock Tickers",
    description=(
        "Fetch data and perform technical analysis on multiple stock tickers concurrently. "
        "Returns lists of successful analyses and failures, preserving the original order of tickers."
    ),
)
async def analyze_stocks(
    request: BatchAnalysisRequest,
    stock_service: StockService = Depends(),
):
    # Normalize inputs to uppercase and strip whitespaces
    raw_tickers = [t.strip().upper() for t in request.tickers if t.strip()]
    if not raw_tickers:
        raise HTTPException(status_code=400, detail="Tickers list cannot be empty.")
    if len(request.tickers) > 10:
        raise HTTPException(
            status_code=400, detail="Batch request exceeds maximum allowed limit of 10 tickers."
        )
    # Deduplicate while preserving insertion order
    tickers = list(dict.fromkeys(raw_tickers))

    async def analyze_single_with_timing(ticker: str):
        ticker_start = time.perf_counter()
        try:
            result = await stock_service.analyze_ticker(ticker)
            duration = time.perf_counter() - ticker_start
            logger.info(f"Analyzed ticker '{ticker}' successfully in {duration:.4f}s")
            return {"status": "success", "ticker": ticker, "data": result}
        except Exception as e:
            duration = time.perf_counter() - ticker_start
            error_msg = str(e)
            logger.error(f"Failed to analyze ticker '{ticker}' after {duration:.4f}s: {error_msg}")
            return {"status": "error", "ticker": ticker, "error": error_msg}

    batch_start = time.perf_counter()
    tasks = [analyze_single_with_timing(ticker) for ticker in tickers]
    task_results = await asyncio.gather(*tasks, return_exceptions=True)
    total_duration = time.perf_counter() - batch_start
    logger.info(f"Batch analysis of {len(tickers)} tickers completed in {total_duration:.4f}s")

    results_list = []
    errors_list = []
    for res in task_results:
        if isinstance(res, Exception):
            logger.critical(f"Unhandled gather exception: {res}")
            continue
        if res["status"] == "success":
            results_list.append(res["data"])
        else:
            errors_list.append(BatchErrorDetail(ticker=res["ticker"], error=res["error"]))
    return BatchAnalysisResponse(results=results_list, errors=errors_list)
