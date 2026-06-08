"""Analysis response schema for AI-native stock analysis.

The schema is strict: all fields are required and validated.
"""

from typing import List, Literal
from pydantic import BaseModel, Field, conint

class AnalysisResponse(BaseModel):
    signal: Literal["BUY", "SELL", "HOLD"] = Field(..., description="Trading signal")
    confidence: conint(ge=0, le=100) = Field(..., description="Confidence score 0-100")
    risk_level: Literal["Low", "Medium", "High", "Unknown"] = Field(..., description="Risk assessment")
    summary: str = Field(..., description="Brief high‑level summary")
    company_overview: str = Field(..., description="Company overview and market relevance")
    technical_analysis: str = Field(..., description="Detailed technical reasoning")
    chart_analysis: str = Field(..., description="Current chart structure analysis")
    trend_analysis: str = Field(..., description="Short‑term, medium‑term, long‑term trend conditions")
    momentum_analysis: str = Field(..., description="Interpretation of RSI, MACD, volume, momentum")
    support_resistance_analysis: str = Field(..., description="Key support/resistance zones and rationale")
    bull_case: str = Field(..., description="Bullish scenario narrative")
    bear_case: str = Field(..., description="Bearish scenario narrative")
    investment_thesis: str = Field(..., description="Core investment thesis")
    position_assessment: str = Field(..., description="Guidance for shareholders and new investors")
    entry_strategy: str = Field(..., description="Suggested entry approach")
    exit_strategy: str = Field(..., description="Suggested exit approach")
    holding_period: str = Field(..., description="Estimated holding period (e.g., 5‑7 trading days)")
    holding_period_rationale: str = Field(..., description="Reasoning for the suggested holding period")
    key_levels: List[str] = Field(..., description="Important support/resistance levels")
    warnings: List[str] = Field(..., description="Risk warnings or caveats")
    setup_quality: str = Field(..., description="Overall quality of the trade setup (high/medium/low)")
    market_bias: str = Field(..., description="Overall market bias (bullish/bearish/neutral)")
    catalyst_summary: str = Field(..., description="Key catalysts influencing the recommendation")
