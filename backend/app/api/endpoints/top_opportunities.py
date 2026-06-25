import asyncio
import csv
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, Query

from app.schemas.ranked_opportunity_response import RankedOpportunityResponse
from app.services.stock_service import StockService
from app.utils.cache import cache

logger = logging.getLogger("app.api.endpoints.top_opportunities")
router = APIRouter()

# Token safety: this scanner does NOT call AI.
# Do not add Gemini/OpenAI here without explicit user confirmation.

APP_DIR = Path(__file__).resolve().parents[2]
INDIA_UNIVERSE_PATH = APP_DIR / "data" / "india_universe.csv"
SCANNER_CONCURRENCY_LIMIT = 15

MARKET_UNIVERSES: Dict[str, List[str]] = {
    "US": [
        "AAPL", "MSFT", "NVDA", "AMZN", "META",
        "GOOGL", "TSLA", "AMD", "NFLX", "AVGO",
        "JPM", "UNH", "XOM", "COST", "CRM",
    ],
}


def _clamp(value: int, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, value))


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        result = float(value)
        if result != result:  # NaN check
            return default
        return result
    except Exception:
        return default


def _parse_enabled(value: Any) -> bool:
    if value is None:
        return True

    return str(value).strip().lower() in {"true", "1", "yes", "y", "on", "enabled"}


def _normalize_india_symbol(symbol: str) -> str:
    clean = str(symbol or "").strip().upper()

    if not clean:
        return ""

    if clean.endswith(".NS"):
        return clean

    return f"{clean}.NS"


def _display_ticker(ticker: str) -> str:
    clean = str(ticker or "").strip().upper()
    return clean[:-3] if clean.endswith(".NS") else clean


def _market_for_ticker(ticker: str) -> str:
    return "INDIA" if str(ticker).upper().endswith(".NS") else "US"


def _load_india_universe() -> List[str]:
    """
    Loads the Indian stock universe from:
    backend/app/data/india_universe.csv

    Expected columns:
    symbol,name,sector,enabled

    This function never crashes the scanner. Missing/empty/bad CSV returns [].
    """
    if not INDIA_UNIVERSE_PATH.exists():
        logger.warning("India universe CSV missing: %s", INDIA_UNIVERSE_PATH)
        return []

    tickers: List[str] = []
    seen: Set[str] = set()

    try:
        with INDIA_UNIVERSE_PATH.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)

            if not reader.fieldnames or "symbol" not in {name.strip().lower() for name in reader.fieldnames}:
                logger.warning("India universe CSV must contain a symbol column: %s", INDIA_UNIVERSE_PATH)
                return []

            for row in reader:
                normalized_row = {str(k).strip().lower(): v for k, v in row.items() if k is not None}

                if not _parse_enabled(normalized_row.get("enabled", "true")):
                    continue

                symbol = _normalize_india_symbol(str(normalized_row.get("symbol", "")))

                if not symbol or symbol in seen:
                    continue

                seen.add(symbol)
                tickers.append(symbol)

    except Exception as exc:
        logger.warning("Failed to load India universe CSV: %s", exc)
        return []

    return tickers


def _select_tickers(market: str) -> List[str]:
    market = market.upper()

    if market == "US":
        return MARKET_UNIVERSES["US"]

    if market == "INDIA":
        return _load_india_universe()

    if market == "ALL":
        return MARKET_UNIVERSES["US"] + _load_india_universe()

    return MARKET_UNIVERSES["US"]


def _setup_quality(risk_reward_ratio: float, confidence: int, breakout_probability: int) -> str:
    if risk_reward_ratio >= 2.0 and confidence >= 70 and breakout_probability >= 60:
        return "strong"

    if risk_reward_ratio >= 1.5 and confidence >= 55 and breakout_probability >= 45:
        return "average"

    return "weak"


def _volume_score(raw: Dict[str, Any]) -> int:
    volume_ratio = _safe_float(raw.get("volume_ratio"), 0)

    if volume_ratio <= 0:
        volume = _safe_float(raw.get("volume") or raw.get("latest_volume"), 0)
        avg_volume = _safe_float(
            raw.get("avg_volume") or raw.get("average_volume") or raw.get("average_volume_20"),
            0,
        )

        if volume > 0 and avg_volume > 0:
            volume_ratio = volume / avg_volume

    if volume_ratio <= 0:
        return 0

    return _clamp(int((volume_ratio - 1) * 25), 0, 25)


def _is_too_close_to_resistance(price: float, resistance: float, atr: float) -> bool:
    if price <= 0 or resistance <= price:
        return True

    distance_to_resistance = resistance - price
    distance_pct = (distance_to_resistance / price) * 100

    return distance_pct < 1.0 or distance_to_resistance < (0.35 * atr)


def _build_candidate(raw: Dict[str, Any], requested_market: str) -> Optional[Dict[str, Any]]:
    ticker = str(raw.get("ticker", "")).upper()
    market = _market_for_ticker(ticker)

    price = _safe_float(raw.get("price"))
    atr = _safe_float(raw.get("atr"))
    support = _safe_float(raw.get("support"))
    resistance = _safe_float(raw.get("resistance"))
    rsi = _safe_float(raw.get("rsi"), 50)
    alignment = _safe_float(raw.get("alignment_score"), 50)

    ema_trend = str(raw.get("ema_trend", "neutral")).lower()
    macd_trend = str(raw.get("macd_trend", "neutral")).lower()
    price_change_pct = _safe_float(raw.get("price_change_pct"), 0)

    # Base hard filters.
    if price <= 0 or atr <= 0:
        return None

    if support <= 0 or resistance <= 0:
        return None

    if support >= price or resistance <= price:
        return None

    bullish_points = 0
    bearish_points = 0

    bullish_points += 25 if ema_trend == "bullish" else 0
    bullish_points += 25 if macd_trend == "bullish" else 0
    bullish_points += int(alignment * 0.30)
    bullish_points += 10 if 40 <= rsi <= 65 else 0
    bullish_points += 8 if rsi < 35 else 0

    bearish_points += 25 if ema_trend == "bearish" else 0
    bearish_points += 25 if macd_trend == "bearish" else 0
    bearish_points += int((100 - alignment) * 0.30)
    bearish_points += 10 if rsi > 70 else 0

    signal = "BUY" if bullish_points >= bearish_points else "SELL"

    # India scanner is long-only for now.
    if market == "INDIA" and signal != "BUY":
        return None

    if signal == "BUY":
        if _is_too_close_to_resistance(price, resistance, atr):
            return None

        entry_mid = min(price, max(support + 0.50 * atr, price - 0.25 * atr))
        entry_range_min = round(max(0.01, entry_mid - 0.25 * atr), 2)
        entry_range_max = round(max(entry_range_min, min(price + 0.10 * atr, entry_mid + 0.25 * atr)), 2)

        exit_mid = max(resistance, price + 1.50 * atr)
        exit_range_min = round(max(entry_range_max, exit_mid - 0.25 * atr), 2)
        exit_range_max = round(max(exit_range_min, exit_mid + 0.25 * atr), 2)

        stop_loss = round(min(support - 0.50 * atr, entry_range_min - 0.75 * atr), 2)

        risk = entry_mid - stop_loss
        reward = exit_mid - entry_mid

        if exit_range_min <= entry_range_max or stop_loss >= entry_range_min:
            return None

    else:
        entry_mid = max(price, min(resistance - 0.25 * atr, price + 0.25 * atr))
        entry_range_min = round(max(0.01, entry_mid - 0.25 * atr), 2)
        entry_range_max = round(max(entry_range_min, entry_mid + 0.25 * atr), 2)

        exit_mid = min(support, price - 1.50 * atr)
        if exit_mid <= 0:
            return None

        exit_range_min = round(max(0.01, exit_mid - 0.25 * atr), 2)
        exit_range_max = round(max(exit_range_min, exit_mid + 0.25 * atr), 2)

        stop_loss = round(max(resistance + 0.50 * atr, entry_range_max + 0.75 * atr), 2)

        risk = stop_loss - entry_mid
        reward = entry_mid - exit_mid

        if exit_range_max >= entry_range_min or stop_loss <= entry_range_max:
            return None

    if risk <= 0 or reward <= 0:
        return None

    risk_reward_ratio = round(reward / risk, 2)
    expected_profit_pct = round((reward / entry_mid) * 100, 2)

    trend_score = bullish_points if signal == "BUY" else bearish_points
    confidence = _clamp(int(35 + trend_score * 0.45 + risk_reward_ratio * 8 + expected_profit_pct * 1.2))
    breakout_probability = _clamp(int(30 + alignment * 0.35 + risk_reward_ratio * 7 + abs(price_change_pct) * 1.5))
    volume_score = _volume_score(raw)

    # Trade quality hard filters.
    if expected_profit_pct < 3:
        return None

    if risk_reward_ratio < 1.5:
        return None

    if confidence < 55:
        return None

    if breakout_probability < 45:
        return None

    setup_quality = _setup_quality(risk_reward_ratio, confidence, breakout_probability)

    if setup_quality == "weak":
        return None

    rank_score = round(
        expected_profit_pct * 2
        + risk_reward_ratio * 15
        + confidence
        + breakout_probability
        + alignment
        + trend_score
        + volume_score,
        2,
    )

    pros: List[str] = []
    cons: List[str] = []

    if ema_trend == "bullish":
        pros.append("EMA trend is bullish.")
    elif ema_trend == "bearish":
        cons.append("EMA trend is bearish.")

    if macd_trend == "bullish":
        pros.append("MACD trend is bullish.")
    elif macd_trend == "bearish":
        cons.append("MACD trend is bearish.")

    if risk_reward_ratio >= 2:
        pros.append(f"Risk/reward is attractive at {risk_reward_ratio}.")
    else:
        pros.append(f"Risk/reward passes the minimum filter at {risk_reward_ratio}.")

    if alignment >= 65:
        pros.append(f"Multi-timeframe alignment is strong at {alignment}%.")
    elif alignment < 45:
        cons.append(f"Multi-timeframe alignment is weak at {alignment}%.")

    if rsi > 70:
        cons.append("RSI is overbought.")
    elif rsi < 35:
        pros.append("RSI is near oversold/rebound zone.")

    if volume_score > 0:
        pros.append("Volume is stronger than its recent average.")

    reason = (
        f"{_display_ticker(ticker)} passed the scanner filters with an estimated profit of "
        f"{expected_profit_pct}%, {risk_reward_ratio} risk/reward, "
        f"{confidence}% confidence, and {breakout_probability}% breakout probability."
    )

    return {
        "ticker": ticker,
        "display_ticker": _display_ticker(ticker),
        "market": market,
        "signal": signal,
        "confidence": confidence,
        "expected_profit_pct": expected_profit_pct,
        "entry_range_min": entry_range_min,
        "entry_range_max": entry_range_max,
        "exit_range_min": exit_range_min,
        "exit_range_max": exit_range_max,
        "stop_loss": stop_loss,
        "risk_reward_ratio": risk_reward_ratio,
        "breakout_probability": breakout_probability,
        "holding_period": "3-10 trading days",
        "setup_quality": setup_quality,
        "pros": pros or ["No pros provided."],
        "cons": cons or ["No major cons detected by deterministic filters."],
        "reason": reason,
        "rank_score": rank_score,
    }


@router.get("/top-opportunities", response_model=List[RankedOpportunityResponse])
async def get_top_opportunities(
    market: str = Query("ALL", description="Market to scan: US, INDIA, or ALL."),
    force_refresh: bool = Query(False, description="Bypass scanner cache."),
    limit: Optional[int] = Query(10, description="Number of results to return. Max 10."),
) -> List[RankedOpportunityResponse]:
    market = market.upper().strip()
    if market not in {"US", "INDIA", "ALL"}:
        market = "ALL"

    safe_limit = min(max(limit or 10, 1), 10)
    cache_key = f"scanner:top_opportunities:v2:{market}:{safe_limit}"

    if not force_refresh:
        try:
            cached = await cache.get(cache_key)
            if cached:
                return [RankedOpportunityResponse(**item) for item in cached]
        except Exception as exc:
            logger.warning("Top opportunities cache read failed: %s", exc)

    tickers = _select_tickers(market)

    if not tickers:
        logger.warning("No tickers selected for market=%s", market)
        return []

    service = StockService()

    semaphore = asyncio.Semaphore(SCANNER_CONCURRENCY_LIMIT)

    async def analyze_raw(ticker: str) -> Optional[Dict[str, Any]]:
        async with semaphore:
            try:
                raw = await asyncio.wait_for(service.get_raw_analysis_data(ticker), timeout=20)
                return _build_candidate(raw, market)
            except Exception as exc:
                logger.warning("Skipping %s: %s", ticker, exc)
                return None

    results = await asyncio.gather(*(analyze_raw(ticker) for ticker in tickers))
    candidates = [item for item in results if item is not None]

    candidates.sort(
        key=lambda item: item["rank_score"],
        reverse=True,
    )

    top_results = candidates[:safe_limit]

    try:
        await cache.set(cache_key, top_results, ttl=900)
    except Exception as exc:
        logger.warning("Top opportunities cache write failed: %s", exc)

    return [RankedOpportunityResponse(**item) for item in top_results]
