from typing import List, Literal
from pydantic import BaseModel, Field


class RankedOpportunityResponse(BaseModel):
    ticker: str
    display_ticker: str
    market: Literal["US", "INDIA"]
    signal: Literal["BUY", "SELL", "HOLD"]

    confidence: int = Field(ge=0, le=100)
    expected_profit_pct: float

    entry_range_min: float
    entry_range_max: float
    exit_range_min: float
    exit_range_max: float
    stop_loss: float

    risk_reward_ratio: float
    breakout_probability: int = Field(ge=0, le=100)

    holding_period: str
    setup_quality: Literal["weak", "average", "strong"]

    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    reason: str
    rank_score: float
