import asyncio
import logging
import time
from fastapi import APIRouter, Query, HTTPException, Depends
from app.schemas.analysis import (
    StockAnalysisResponse, 
    BatchAnalysisRequest, 
    BatchAnalysisResponse, 
    BatchErrorDetail
)
from app.services.stock_service import StockService

# Setup logger for the endpoint performance logging
logger = logging.getLogger("app.api.endpoints.analysis")

router = APIRouter()

@router.get(
    "/analyze-stock",
    response_model=StockAnalysisResponse,
    summary="Analyze Stock Ticker",
    description=(
        "Fetch historical stock data using yfinance, compute technical indicators "
        "(RSI, MACD, EMA 20, EMA 50) using pandas-ta, and return a structured analysis "
        "consisting of a recommendation, confidence score, pros, and cons."
    )
)
async def analyze_stock(
    ticker: str = Query(
        ..., 
        min_length=1, 
        max_length=10, 
        description="The stock ticker symbol (e.g. NVDA, AAPL, MSFT)"
    ),
    stock_service: StockService = Depends()
):
    try:
        analysis_result = await stock_service.analyze_ticker(ticker)
        return analysis_result
    except ValueError as ve:
        # Expected error from yfinance/data issues: return 400 Bad Request
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # Unexpected errors: return 500 Internal Server Error
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while performing stock analysis: {str(e)}"
        )

@router.post(
    "/analyze-stocks",
    response_model=BatchAnalysisResponse,
    summary="Batch Analyze Stock Tickers",
    description=(
        "Fetch data and perform technical analysis on multiple stock tickers concurrently. "
        "Returns lists of successful analyses and failures, preserving the original order of tickers."
    )
)
async def analyze_stocks(
    request: BatchAnalysisRequest,
    stock_service: StockService = Depends()
):
    # Normalize inputs to uppercase and strip whitespaces
    raw_tickers = [t.strip().upper() for t in request.tickers if t.strip()]

    if not raw_tickers:
        raise HTTPException(status_code=400, detail="Tickers list cannot be empty.")

    # Enforce request cap of 10 items on the raw input (before or after deduplication)
    # The requirement says "cap requests at maximum 10 tickers"
    if len(request.tickers) > 10:
        raise HTTPException(
            status_code=400,
            detail="Batch request exceeds maximum allowed limit of 10 tickers."
        )

    # Deduplicate while preserving insertion order using dict.fromkeys
    tickers = list(dict.fromkeys(raw_tickers))

    # Helper function to track per-ticker analysis execution duration
    async def analyze_single_with_timing(ticker: str):
        ticker_start = time.perf_counter()
        try:
            result = await stock_service.analyze_ticker(ticker)
            duration = time.perf_counter() - ticker_start
            logger.info(f"Analyzed ticker '{ticker}' successfully in {duration:.4f}s")
            return {
                "status": "success",
                "ticker": ticker,
                "data": result
            }
        except Exception as e:
            duration = time.perf_counter() - ticker_start
            error_msg = str(e)
            logger.error(f"Failed to analyze ticker '{ticker}' after {duration:.4f}s: {error_msg}")
            return {
                "status": "error",
                "ticker": ticker,
                "error": error_msg
            }

    # Start total batch execution timing
    batch_start = time.perf_counter()

    # Create and schedule concurrent tasks
    tasks = [analyze_single_with_timing(ticker) for ticker in tickers]
    
    # asyncio.gather runs all tasks concurrently and preserves the order of results
    task_results = await asyncio.gather(*tasks, return_exceptions=True)

    total_duration = time.perf_counter() - batch_start
    logger.info(f"Batch analysis of {len(tickers)} tickers completed in {total_duration:.4f}s")

    results_list = []
    errors_list = []

    # Distribute task results into successful and failed arrays preserving order
    for res in task_results:
        # Check if gather caught an unhandled exception outside our timing wrapper
        if isinstance(res, Exception):
            # This shouldn't normally happen since analyze_single_with_timing handles exceptions internally
            logger.critical(f"Unhandled gather exception: {str(res)}")
            continue

        if res["status"] == "success":
            results_list.append(res["data"])
        else:
            errors_list.append(
                BatchErrorDetail(ticker=res["ticker"], error=res["error"])
            )

    return BatchAnalysisResponse(results=results_list, errors=errors_list)


