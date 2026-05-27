import asyncio
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import logging
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

    async def analyze_ticker(self, ticker: str) -> Dict[str, Any]:
        """Analyze a ticker across multiple timeframes (1D, 4H, 1H).
        Returns a dictionary containing technical indicators for each timeframe,
        trade‑setup fields, risk/reward ratio and an alignment score.
        """
        ticker_clean = ticker.strip().upper()

        # Define intervals per timeframe (yfinance supported intervals)
        intervals = {"1D": "1d", "4H": "4h", "1H": "1h"}

        # Fetch data for all intervals with caching to avoid duplicate Yahoo Finance calls
        async def fetch_interval(iv: str) -> pd.DataFrame:
            cache_key = ("historical", ticker_clean, iv)
            async def compute():
                # Run the blocking fetch in a thread to keep async flow
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

        # Compute and cache indicators per timeframe
        async def get_indicators(tf: str, df: pd.DataFrame) -> Dict[str, Any]:
            cache_key = ("indicators", ticker_clean, tf)
            async def compute():
                return compute_indicators(df)
            return await cache.get_or_compute(
                cache_key,
                settings.CACHE_TTL_SECONDS,
                compute,
                cache_name="indicators",
            )

        timeframe_stats = {}
        for tf, df in df_map.items():
            timeframe_stats[tf] = await get_indicators(tf, df)

        
        # Build a summary of overall trends per timeframe for API consumers
        timeframe_summary = {tf: {"trend": stats["trend"]} for tf, stats in timeframe_stats.items()}

        # Daily dataframe is used for trade‑setup calculations (ATR, BB, support/resistance, etc.)
        df_daily = df_map["1D"]
        if df_daily.empty:
            raise ValueError(f"No historical data found for ticker '{ticker_clean}'.")
        if len(df_daily) < 50:
            raise ValueError(f"Insufficient data for EMA calculations for '{ticker_clean}'.")

        # Compute daily technical indicators
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

        # Additional trade‑setup indicators
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

        # Core scoring algorithm (0‑100)
        score = 50
        # EMA trend
        score += 15 if ema_trend == "bullish" else -15
        # MACD trend
        score += 15 if macd_trend == "bullish" else -15
        # RSI weighting
        if rsi_val < 30:
            score += 20
        elif rsi_val < 40:
            score += 10
        elif rsi_val > 70:
            score -= 20
        elif rsi_val > 60:
            score -= 10
        # Price vs EMA20
        score += 10 if price > ema_20 else -10
        # Volume confirmation
        if latest_vol > avg_vol:
            score += 10 if price_change_pct > 0 else -10
        # Clamp score
        score = max(0, min(100, score))

        # Build pros/cons
        pros: List[str] = []
        cons: List[str] = []
        if ema_trend == "bullish":
            pros.append("Bullish long‑term trend (20 EMA above 50 EMA)")
        else:
            cons.append("Bearish long‑term trend (20 EMA below 50 EMA)")
        if macd_trend == "bullish":
            pros.append("Bullish MACD crossover (MACD line above signal)")
        else:
            cons.append("Bearish MACD crossover (MACD line below signal)")
        if rsi_val < 30:
            pros.append(f"Oversold (RSI = {rsi_val:.1f})")
        elif rsi_val < 40:
            pros.append(f"Favorable RSI (RSI = {rsi_val:.1f})")
        elif rsi_val > 70:
            cons.append(f"Overbought (RSI = {rsi_val:.1f})")
        elif rsi_val > 60:
            cons.append(f"Elevated RSI (RSI = {rsi_val:.1f})")
        if price > ema_20:
            pros.append("Price above 20 EMA (positive momentum)")
        else:
            cons.append("Price below 20 EMA (negative momentum)")
        if latest_vol > avg_vol:
            if price_change_pct > 0:
                pros.append("Strong buying volume confirms upward pressure")
            else:
                cons.append("High volume sell‑off suggests downward pressure")

        # Signal determination
        if score >= 65:
            signal = "BUY"
            confidence = int(score)
        elif score <= 35:
            signal = "SELL"
            confidence = int(100 - score)
        else:
            signal = "HOLD"
            confidence = int(100 - abs(score - 50) * 2)

        # Trade‑setup calculations
        atr = float(df_daily['ATR'].iloc[-1]) if not pd.isna(df_daily['ATR'].iloc[-1]) else 0.0
        support = float(df_daily['support'].iloc[-1]) if not pd.isna(df_daily['support'].iloc[-1]) else price * 0.95
        resistance = float(df_daily['resistance'].iloc[-1]) if not pd.isna(df_daily['resistance'].iloc[-1]) else price * 1.05
        entry_min = round(support + 0.5 * atr, 2)
        if signal == "BUY":
            entry_max = round(min(support + atr, price), 2)
        else:
            entry_max = round(support + atr, 2)

        # Determine entry quality and breakout probability based on proximity to S/R levels
        if signal == "BUY":
            entry_quality = "strong" if (price - support) < (0.5 * atr) else "moderate"
            if price > resistance:
                breakout_probability = 80
            elif (price - support) < (0.5 * atr):
                breakout_probability = 60
            else:
                breakout_probability = 40
        elif signal == "SELL":
            entry_quality = "strong" if (resistance - price) < (0.5 * atr) else "moderate"
            if price < support:
                breakout_probability = 80
            elif (resistance - price) < (0.5 * atr):
                breakout_probability = 60
            else:
                breakout_probability = 40
        else:
            entry_quality = "moderate"
            breakout_probability = 50
        entry_price = (entry_min + entry_max) / 2
        # Stop‑loss using configurable multipliers
        if signal == "BUY":
            stop_loss = round(entry_price - atr * settings.STOP_LOSS_BUY_MULTIPLIER, 2)
        else:
            stop_loss = round(entry_price + atr * settings.STOP_LOSS_SELL_MULTIPLIER, 2)
        # Take‑profit using configurable multipliers
        if signal == "BUY":
            tp1 = round(entry_price + atr * settings.TAKE_PROFIT_BUY_MULTIPLIER, 2)
            tp2 = round(entry_price + atr * settings.TAKE_PROFIT_BUY_MULTIPLIER * 2, 2)
        else:
            tp1 = round(entry_price - atr * settings.TAKE_PROFIT_SELL_MULTIPLIER, 2)
            tp2 = round(entry_price - atr * settings.TAKE_PROFIT_SELL_MULTIPLIER * 2, 2)
        risk_reward_ratio = round(((tp1 - entry_price) / (entry_price - stop_loss)) if (entry_price - stop_loss) != 0 else 0, 2)
        # Volatility level based on ATR relative to price
        vol_ratio = atr / price if price != 0 else 0
        if vol_ratio >= settings.VOLATILITY_HIGH_RATIO:
            volatility_level = "high"
        elif vol_ratio >= settings.VOLATILITY_MEDIUM_RATIO:
            volatility_level = "medium"
        else:
            volatility_level = "low"

        # Alignment score – average of timeframe EMA trends weighted by RSI proximity to 50
        alignment_components = []
        weight_map = {"1D": 3, "4H": 2, "1H": 1}
        alignment_components = []
        total_weight = 0
        for tf, stats in timeframe_stats.items():
            trend = stats["trend"]
            trend_score = 1 if trend == "bullish" else (0 if trend == "bearish" else 0.5)
            rsi_factor = 1 - abs(stats["rsi"] - 50) / 50
            w = weight_map.get(tf, 1)
            alignment_components.append(trend_score * rsi_factor * w)
            total_weight += w
        alignment_score = round(sum(alignment_components) / total_weight * 100, 1) if total_weight else 0
        # Adjust confidence based on alignment (max +/-10 points)
        confidence = max(0, min(100, confidence + int((alignment_score - 50) * 0.2)))

        response: Dict[str, Any] = {
            "ticker": ticker_clean,
            "price": round(price, 2),
            "signal": signal,
            "confidence": confidence,
            "rsi": round(rsi_val, 1),
            "macd": macd_trend,
            "ema_trend": ema_trend,
            "pros": pros if pros else ["Indicators are in a neutral state."],
            "cons": cons if cons else ["No major negative indicators found."],
            "entry_zone": {"min": entry_min, "max": entry_max},
            "stop_loss": stop_loss,
            "take_profit": {"tp1": tp1, "tp2": tp2},
            "holding_period": (
                "5-7 trading days" if (atr / price) * 100 < 1 else
                "3-5 trading days" if (atr / price) * 100 < 2 else
                "1-3 trading days"
            ),
            "risk_reward_ratio": risk_reward_ratio,
            "atr": round(atr, 2),
            "volatility_level": volatility_level,
            "nearest_support": support,
            "nearest_resistance": resistance,
            "entry_quality": entry_quality,
            "breakout_probability": breakout_probability,
            "setup_quality": (
                "high" if risk_reward_ratio >= settings.RISK_REWARD_THRESHOLD else
                "medium" if risk_reward_ratio >= 1.0 else
                "low"
            ),
            "timeframes": timeframe_stats,
            "timeframe_summary": timeframe_summary,
            "alignment_score": alignment_score,
        }
        return response
