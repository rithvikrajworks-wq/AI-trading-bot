import pandas as pd
import pandas_ta as ta
from typing import Dict, Any, Union


def _ta_single_series(result: Union[pd.Series, pd.DataFrame]) -> pd.Series:
    if isinstance(result, pd.DataFrame):
        return result.iloc[:, 0]
    if isinstance(result, pd.Series):
        return result
    raise TypeError(f"Unexpected pandas_ta result type: {type(result)}")


def compute_indicators(df: pd.DataFrame) -> Dict[str, Any]:
    """Compute the common technical indicators used throughout the app.
    Returns a dictionary with the same keys as the previous in‑line implementation.
    """
    # Ensure TA columns exist
    df['RSI'] = _ta_single_series(df.ta.rsi(length=14))
    df['EMA_20'] = _ta_single_series(df.ta.ema(length=20))
    df['EMA_50'] = _ta_single_series(df.ta.ema(length=50))
    macd_df = df.ta.macd(fast=12, slow=26, signal=9)

    latest_row = df.iloc[-1]
    latest_macd = macd_df.iloc[-1]

    rsi_val = float(latest_row['RSI']) if not pd.isna(latest_row['RSI']) else 50.0
    ema_20 = float(latest_row['EMA_20'])
    ema_50 = float(latest_row['EMA_50'])
    macd_line = float(latest_macd.iloc[0])
    macd_signal = float(latest_macd.iloc[2])

    ema_trend = "bullish" if ema_20 > ema_50 else "bearish"
    macd_trend = "bullish" if macd_line > macd_signal else "bearish"
    momentum = float(latest_row['Close']) - ema_20

    if ema_trend == "bullish" and macd_trend == "bullish" and momentum > 0:
        overall_trend = "bullish"
    elif ema_trend == "bearish" and macd_trend == "bearish" and momentum < 0:
        overall_trend = "bearish"
    else:
        overall_trend = "neutral"

    return {
        "rsi": round(rsi_val, 1),
        "ema_trend": ema_trend,
        "macd_trend": macd_trend,
        "momentum": round(momentum, 2),
        "trend": overall_trend,
    }
