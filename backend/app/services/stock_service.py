import asyncio
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import logging
import json
from app.utils.cache import cache
from app.utils.indicators import compute_indicators
from app.core.config import settings

logger = logging.getLogger(__name__)
from typing import Dict, Any, List


class StockService:
    @staticmethod
    def _fetch_history(ticker: str, interval: str = "1d") -> pd.DataFrame:
        """Fetch historical data for a ticker using yfinance.
        Runs synchronously but should be called via a thread pool to avoid blocking.
        """
        stock = yf.Ticker(ticker)
        # 1 year of data for stability of longer indicators
        df = stock.history(period="1y", interval=interval)
        return df

    async def get_raw_analysis_data(self, ticker: str) -> Dict[str, Any]:
        """Fetch raw market indicators without any trading decision logic."""
        ticker_clean = ticker.strip().upper()
        intervals = {"1D": "1d", "4H": "4h", "1H": "1h"}

        async def fetch_interval(iv: str) -> pd.DataFrame:
            cache_key = ("historical", ticker_clean, iv)
            async def compute():
                return await asyncio.to_thread(self._fetch_history, ticker_clean, iv)
            return await cache.get_or_compute(
                cache_key,
                settings.CACHE_TTL_SECONDS,
                compute,
                cache_name="historical_data",
            )

        fetch_tasks = [fetch_interval(iv) for iv in intervals.values()]
        dfs = await asyncio.gather(*fetch_tasks)
        df_map: Dict[str, pd.DataFrame] = dict(zip(intervals.keys(), dfs))

        async def get_indicators(tf: str, df: pd.DataFrame) -> Dict[str, Any]:
            cache_key = ("indicators", ticker_clean, tf)
            async def compute_tf():
                return compute_indicators(df)
            return await cache.get_or_compute(
                cache_key,
                settings.CACHE_TTL_SECONDS,
                compute_tf,
                cache_name="indicators",
            )

        timeframe_stats = {}
        for tf, df in df_map.items():
            timeframe_stats[tf] = await get_indicators(tf, df)

        timeframe_summary = {tf: {"trend": stats["trend"]} for tf, stats in timeframe_stats.items()}

        df_daily = df_map["1D"]
        if df_daily.empty:
            raise ValueError(f"No historical data found for ticker '{ticker_clean}'.")
        if len(df_daily) < 50:
            raise ValueError(f"Insufficient data for EMA calculations for '{ticker_clean}'.")

        df_daily['RSI'] = df_daily.ta.rsi(length=14)
        df_daily['EMA_20'] = df_daily.ta.ema(length=20)
        df_daily['EMA_50'] = df_daily.ta.ema(length=50)
        macd_daily = df_daily.ta.macd(fast=12, slow=26, signal=9)
        latest_row = df_daily.iloc[-1]
        latest_macd = macd_daily.iloc[-1]
        price = float(latest_row['Close'])
        rsi_val = float(latest_row['RSI']) if not pd.isna(latest_row['RSI']) else 50.0
        ema_20 = float(latest_row['EMA_20'])
        ema_50 = float(latest_row['EMA_50'])
        macd_line = float(latest_macd.iloc[0])
        macd_signal = float(latest_macd.iloc[2])
        ema_trend = "bullish" if ema_20 > ema_50 else "bearish"
        macd_trend = "bullish" if macd_line > macd_signal else "bearish"

        df_daily['ATR'] = df_daily.ta.atr(length=14)
        bb = df_daily.ta.bbands(length=20, std=2)
        df_daily = df_daily.join(bb)
        df_daily['support'] = df_daily['Low'].rolling(20).min()
        df_daily['resistance'] = df_daily['High'].rolling(20).max()
        df_daily['Vol_MA20'] = df_daily['Volume'].rolling(20).mean()
        latest_vol = float(latest_row['Volume'])
        avg_vol = float(df_daily['Vol_MA20'].iloc[-1]) if not pd.isna(df_daily['Vol_MA20'].iloc[-1]) else latest_vol
        yesterday_close = float(df_daily['Close'].iloc[-2]) if len(df_daily) > 1 else price
        price_change_pct = ((price - yesterday_close) / yesterday_close) * 100 if yesterday_close != 0 else 0

        atr = float(df_daily['ATR'].iloc[-1]) if not pd.isna(df_daily['ATR'].iloc[-1]) else 0.0
        support = float(df_daily['support'].iloc[-1]) if not pd.isna(df_daily['support'].iloc[-1]) else price * 0.95
        resistance = float(df_daily['resistance'].iloc[-1]) if not pd.isna(df_daily['resistance'].iloc[-1]) else price * 1.05

        alignment_components = []
        weight_map = {"1D": 3, "4H": 2, "1H": 1}
        total_weight = 0
        for tf, stats in timeframe_stats.items():
            trend = stats["trend"]
            trend_score = 1 if trend == "bullish" else (0 if trend == "bearish" else 0.5)
            rsi_factor = 1 - abs(stats["rsi"] - 50) / 50
            w = weight_map.get(tf, 1)
            alignment_components.append(trend_score * rsi_factor * w)
            total_weight += w
        alignment_score = round(sum(alignment_components) / total_weight * 100, 1) if total_weight else 0

        return {
            "ticker": ticker_clean,
            "price": round(price, 2),
            "rsi": round(rsi_val, 1),
            "macd_trend": macd_trend,
            "ema_trend": ema_trend,
            "atr": round(atr, 2),
            "support": round(support, 2),
            "resistance": round(resistance, 2),
            "latest_volume": latest_vol,
            "average_volume_20": avg_vol,
            "price_change_pct": round(price_change_pct, 2),
            "timeframe_stats": timeframe_stats,
            "timeframe_summary": timeframe_summary,
            "alignment_score": alignment_score,
        }

    async def fetch_market_data(self, ticker: str) -> Dict[str, Any]:
        """Backward compatible delegate to get_raw_analysis_data."""
        return await self.get_raw_analysis_data(ticker)

    async def analyze_ticker(self, ticker: str) -> Dict[str, Any]:
        """Analyze ticker by invoking Gemini (via AnalysisAgent).
        This replaces the deterministic Python trading logic.
        """
        raw_data = await self.get_raw_analysis_data(ticker)
        
        # Import AnalysisAgent inside to avoid circular imports if any
        from app.agents.analysis_agent import AnalysisAgent
        agent = AnalysisAgent()
        ai_response = await agent.analyze(ticker=raw_data["ticker"], market_data=raw_data)

        # Build trade setup details mathematically (infrastructure logic allowed by spec)
        signal = ai_response.signal
        atr = raw_data["atr"]
        price = raw_data["price"]
        support = raw_data["support"]
        resistance = raw_data["resistance"]

        entry_min = round(support + 0.5 * atr, 2)
        if signal == "BUY":
            entry_max = round(min(support + atr, price), 2)
        else:
            entry_max = round(support + atr, 2)
        entry_price = (entry_min + entry_max) / 2

        if signal == "BUY":
            stop_loss = round(entry_price - atr * settings.STOP_LOSS_BUY_MULTIPLIER, 2)
            tp1 = round(entry_price + atr * settings.TAKE_PROFIT_BUY_MULTIPLIER, 2)
            tp2 = round(entry_price + atr * settings.TAKE_PROFIT_BUY_MULTIPLIER * 2, 2)
        else:
            stop_loss = round(entry_price + atr * settings.STOP_LOSS_SELL_MULTIPLIER, 2)
            tp1 = round(entry_price - atr * settings.TAKE_PROFIT_SELL_MULTIPLIER, 2)
            tp2 = round(entry_price - atr * settings.TAKE_PROFIT_SELL_MULTIPLIER * 2, 2)

        risk_reward_ratio = round(((tp1 - entry_price) / (entry_price - stop_loss)) if (entry_price - stop_loss) != 0 else 0, 2)
        
        # Determine breakout probability based on risk/signal (AI narrative risk)
        breakout_probability = 50
        if signal == "BUY":
            if price > resistance:
                breakout_probability = 80
            elif (price - support) < (0.5 * atr):
                breakout_probability = 60
        elif signal == "SELL":
            if price < support:
                breakout_probability = 80
            elif (resistance - price) < (0.5 * atr):
                breakout_probability = 60

        # Construct final dict matching StockAnalysisResponse schema
        return {
            "ticker": raw_data["ticker"],
            "price": price,
            "signal": signal,
            "confidence": ai_response.confidence,
            "rsi": raw_data["rsi"],
            "macd": raw_data["macd_trend"],
            "ema_trend": raw_data["ema_trend"],
            "pros": [ai_response.summary],
            "cons": ai_response.warnings if ai_response.warnings else ["No major negative indicators found."],
            "entry_zone": {"min": entry_min, "max": entry_max},
            "stop_loss": stop_loss,
            "take_profit": {"tp1": tp1, "tp2": tp2},
            "holding_period": ai_response.holding_period,
            "risk_reward_ratio": risk_reward_ratio,
            "atr": atr,
            "volatility_level": ai_response.risk_level.lower(),
            "setup_quality": ai_response.setup_quality.lower(),
            "nearest_support": support,
            "nearest_resistance": resistance,
            "entry_quality": "moderate",
            "breakout_probability": breakout_probability,
            "timeframes": raw_data["timeframe_stats"],
            "timeframe_summary": raw_data["timeframe_summary"],
            "alignment_score": raw_data["alignment_score"],
        }

