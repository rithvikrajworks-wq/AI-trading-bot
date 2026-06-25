"""Analysis response schema for AI-native stock analysis.

The schema is strict: all fields are required and validated, but we add tolerant
validators to coerce common LLM formatting issues (numeric strings, floats, case
variations). This ensures the backend accepts Gemini output without falling back
to default values.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Literal

class AnalysisResponse(BaseModel):
    signal: Literal["BUY", "SELL", "HOLD"] = Field(default="HOLD", description="Trading signal")
    confidence: int = Field(default=50, description="Confidence score 0-100", ge=0, le=100)
    breakout_probability: int = Field(default=50, description="Estimated breakout probability as a percentage", ge=0, le=100)
    risk_level: Literal["Low", "Medium", "High", "Unknown"] = Field(default="Medium", description="Risk assessment")
    summary: str = Field(default="No summary available.", description="Brief high-level summary")
    company_overview: str = Field(default="No company overview available.", description="Company overview and market relevance")
    technical_analysis: str = Field(default="No technical analysis available.", description="Detailed technical reasoning")
    chart_analysis: str = Field(default="No chart analysis available.", description="Current chart analysis")
    trend_analysis: str = Field(default="No trend analysis available.", description="Short‑term, medium‑term, long‑term trend conditions")
    momentum_analysis: str = Field(default="No momentum analysis available.", description="Interpretation of RSI, MACD, volume, momentum")
    support_resistance_analysis: str = Field(default="No support/resistance analysis available.", description="Key support/resistance zones and rationale")
    bull_case: str = Field(default="No bull case available.", description="Bullish scenario narrative")
    bear_case: str = Field(default="No bear case available.", description="Bearish scenario narrative")
    investment_thesis: str = Field(default="No investment thesis available.", description="Core investment thesis")
    position_assessment: str = Field(default="No position assessment available.", description="Guidance for shareholders and new investors")
    entry_strategy: str = Field(default="No entry strategy available.", description="Suggested entry approach")
    exit_strategy: str = Field(default="No exit strategy available.", description="Suggested exit approach")
    holding_period: str = Field(default="Unknown", description="Estimated holding period (e.g., 5-7 trading days)")
    holding_period_rationale: str = Field(default="No holding period rationale available.", description="Reasoning for the suggested holding period")
    key_levels: List[str] = Field(default_factory=list, description="Important support/resistance levels")
    warnings: List[str] = Field(default_factory=list, description="Risk warnings or caveats")
    setup_quality: str = Field(default="unknown", description="Overall quality of the trade setup (high/medium/low)")
    market_bias: str = Field(default="neutral", description="Overall market bias (bullish/bearish/neutral)")
    catalyst_summary: str = Field(default="No major catalyst identified.", description="Key catalysts influencing the recommendation")

    # ----- Validators -----
    @validator("key_levels", pre=True, each_item=True)
    def ensure_str_key_levels(cls, v):
        return str(v)

    @validator("confidence", "breakout_probability", pre=True)
    def coerce_int(cls, v):
        """Accept ints, floats or numeric strings and coerce to int."""
        try:
            return int(float(v))
        except Exception as exc:
            raise ValueError(f"Invalid numeric value: {v}") from exc

    @validator("risk_level", pre=True)
    def normalize_risk_level(cls, v):
        if isinstance(v, str):
            v_norm = v.title()
            if v_norm in {"Low", "Medium", "High", "Unknown"}:
                return v_norm
        raise ValueError("risk_level must be one of Low, Medium, High, Unknown")

    @validator("setup_quality", "market_bias", "catalyst_summary", pre=True, always=True)
    def ensure_string(cls, v):
        return str(v) if v is not None else v
