# backend/app/schemas/portfolio.py
"""
File path: Tradingbotmk1/backend/app/schemas/portfolio.py
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

# Enums / literals
MarketType = Literal["US", "INDIA"]
StatusType = Literal["holding", "watching", "sold"]

# Base – shared fields used by Create + Update + DB
class PortfolioBase(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=20, examples=["AAPL", "RELIANCE"])
    market: MarketType = Field(..., examples=["US", "INDIA"])
    quantity: float = Field(..., gt=0, examples=[10.0])
    average_cost: float = Field(..., gt=0, examples=[150.00])
    current_price: float = Field(..., ge=0, examples=[175.50])
    status: StatusType = Field(default="holding")
    notes: Optional[str] = Field(default=None, max_length=500)

# Create schema – what the frontend POSTs
class PortfolioCreate(PortfolioBase):
    pass

# Update schema – all fields optional for PATCH
class PortfolioUpdate(BaseModel):
    market: Optional[MarketType] = None
    quantity: Optional[float] = Field(default=None, gt=0)
    average_cost: Optional[float] = Field(default=None, gt=0)
    current_price: Optional[float] = Field(default=None, ge=0)
    status: Optional[StatusType] = None
    notes: Optional[str] = Field(default=None, max_length=500)

# Response schema – what we return (includes computed fields)
class PortfolioResponse(BaseModel):
    id: int
    ticker: str
    market: MarketType
    quantity: float
    average_cost: float
    current_price: float
    status: StatusType
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    invested_amount: float
    current_value: float
    profit_loss: float
    profit_loss_pct: float

    model_config = {"from_attributes": True}

# Summary schema – aggregate stats for /portfolio/summary
class PortfolioSummary(BaseModel):
    total_invested: float
    total_current_value: float
    total_profit_loss: float
    total_profit_loss_pct: float
    holdings_count: int
    watching_count: int
    sold_count: int
