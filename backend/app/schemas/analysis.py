from pydantic import BaseModel, Field
from typing import List, Dict, Any


class StockAnalysisResponse(BaseModel):
    ticker: str = Field(..., description="The stock ticker symbol", examples=["NVDA"])
    price: float = Field(..., description="The current close price of the stock", examples=[924.21])
    signal: str = Field(..., description="Suggested action: BUY, SELL, or HOLD", examples=["BUY"])
    confidence: int = Field(..., description="Confidence score of the signal, range 0 to 100", examples=[84], ge=0, le=100)
    rsi: float = Field(..., description="Relative Strength Index value", examples=[38.0])
    macd: str = Field(..., description="MACD trend (bullish or bearish)", examples=["bullish"])
    ema_trend: str = Field(..., description="EMA trend based on 20 and 50 period EMAs (bullish if EMA 20 > EMA 50)", examples=["bullish"])
    pros: List[str] = Field(..., description="Positive factors supporting the signal", examples=[["Bullish MACD crossover", "Strong volume trend"]])
    cons: List[str] = Field(..., description="Negative factors or risks to consider", examples=[["Near resistance", "High volatility"]])
    # Trade‑setup fields
    entry_zone: Dict[str, float] = Field(..., description="Suggested entry price range with keys 'min' and 'max'", examples=[{"min": 3420, "max": 3450}])
    stop_loss: float = Field(..., description="Dynamic stop‑loss price based on ATR and support", examples=[3360])
    take_profit: Dict[str, float] = Field(..., description="Take‑profit targets TP1 and TP2", examples=[{"tp1": 3520, "tp2": 3610}])
    holding_period: str = Field(..., description="Estimated holding duration, e.g., '3-7 trading days'", examples=["3-7 trading days"])
    # Risk/Reward ratio (reward / risk) – higher is better, rounded to 2 decimals
    risk_reward_ratio: float = Field(..., description="Risk/Reward ratio calculated as (TP1 - entry_price) / (entry_price - stop_loss)", examples=[2.35])
    atr: float = Field(..., description="Average True Range (ATR) value for the ticker", examples=[48.2])
    volatility_level: str = Field(..., description="Volatility classification: \"high\", \"medium\", or \"low\" based on ATR relative to price", examples=["medium"])
    setup_quality: str = Field(..., description="Overall setup quality: \"high\", \"medium\", or \"low\" based on risk/reward and volatility", examples=["high"])
    nearest_support: float = Field(..., description="Nearest support level derived from recent swing lows", examples=[3380])
    nearest_resistance: float = Field(..., description="Nearest resistance level derived from recent swing highs", examples=[3615])
    entry_quality: str = Field(..., description="Entry quality rating: \"excellent\", \"strong\", \"moderate\", or \"weak\"", examples=["strong"])
    breakout_probability: int = Field(..., description="Estimated breakout probability as a percentage", examples=[74])

    # Multi‑timeframe analysis results
    timeframes: Dict[str, Any] = Field(..., description="Technical indicators per timeframe (1D, 4H, 1H)")
    timeframe_summary: Dict[str, Any] = Field(..., description="Aggregated trend summary per timeframe (bullish, bearish, neutral)")
    alignment_score: float = Field(..., description="Overall alignment score based on timeframe trends", examples=[78.5])


class BatchErrorDetail(BaseModel):
    ticker: str = Field(..., description="The stock ticker symbol that failed to analyze", examples=["INVALID"])
    error: str = Field(..., description="The error message details", examples=["Ticker not found"])


class BatchAnalysisRequest(BaseModel):
    tickers: List[str] = Field(
        ..., min_length=1, max_length=10,
        description="List of stock ticker symbols to analyze (1 to 10 tickers)",
        examples=[["NVDA", "AAPL", "MSFT"]]
    )


class BatchAnalysisResponse(BaseModel):
    results: List[StockAnalysisResponse] = Field(
        default_factory=list,
        description="List of successful stock analyses preserving original insertion order"
    )
    errors: List[BatchErrorDetail] = Field(
        default_factory=list,
        description="List of failed stock analyses preserving original insertion order"
    )
