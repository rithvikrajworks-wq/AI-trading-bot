from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ChatRequest(BaseModel):
    ticker: str = Field(..., description="Ticker symbol to discuss, e.g., 'NVDA'")
    user_message: str = Field(..., description="User's question or comment about the ticker")
    conversation_history: Optional[List[Dict[str, str]]] = Field(
        None,
        description="Optional list of prior messages in the format {'role': 'user'|'assistant', 'content': str}",
    )
    market_context: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional additional market context, such as sector trends or macro data",
    )

class AnalysisSummary(BaseModel):
    timeframe_summary: Dict[str, Any]
    rsi: float
    ema_trend: str
    macd: str
    momentum: float
    alignment_score: float
    confidence: int
    entry_quality: str
    breakout_probability: int
    atr: float
    volatility_level: str
    nearest_support: float
    nearest_resistance: float
    risk_reward_ratio: float
    stop_loss: float
    take_profit: Dict[str, float]

class RiskSummary(BaseModel):
    support_resistance_risk: str
    volatility_risk: str
    alignment_conflict: str
    overall_risk: str

class ChatResponse(BaseModel):
    ticker: str
    response: str
    analysis_summary: AnalysisSummary
    risk_summary: RiskSummary
