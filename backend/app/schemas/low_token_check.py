from pydantic import BaseModel, Field
from typing import Literal

class LowTokenCheckRequest(BaseModel):
    """Request body for low‑token analysis mode."""
    ticker: str = Field(..., min_length=1, max_length=10, description="Ticker symbol")
    mode: Literal["low_token"] = Field(..., description="Analysis mode – only 'low_token' supported")

class LowTokenCheckResponse(BaseModel):
    """Lightweight response indicating if a full analysis is worthwhile."""
    ticker: str
    worth_analysis: bool
    reason: str
    estimated_setup_quality: Literal["low", "medium", "high"]
    suggested_next_mode: Literal["normal_analysis", "trading_committee", "risk_reward", "skip"]