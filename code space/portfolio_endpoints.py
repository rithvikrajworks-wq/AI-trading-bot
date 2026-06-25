"""
File path: Tradingbotmk1/backend/app/api/endpoints/portfolio.py

This file contains:
  1. The SQLAlchemy ORM model  (Portfolio)
  2. DB helper                 (get_db)
  3. All 5 FastAPI endpoints
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# ---------------------------------------------------------------------------
# Database setup
# Adjust DATABASE_URL to match your existing db path if needed.
# ---------------------------------------------------------------------------

DATABASE_URL = "sqlite:///./tradingbot.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


# ---------------------------------------------------------------------------
# ORM Model
# ---------------------------------------------------------------------------

class Portfolio(Base):
    __tablename__ = "portfolio"

    id            = Column(Integer, primary_key=True, index=True)
    ticker        = Column(String(20), unique=True, nullable=False, index=True)
    market        = Column(String(10), nullable=False)          # "US" | "INDIA"
    quantity      = Column(Float, nullable=False)
    average_cost  = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False, default=0.0)
    status        = Column(String(20), nullable=False, default="holding")  # holding | watching | sold
    notes         = Column(Text, nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)
    updated_at    = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # -----------------------------------------------------------------
    # Computed properties – derived deterministically, never stored
    # -----------------------------------------------------------------

    @property
    def invested_amount(self) -> float:
        return round(self.quantity * self.average_cost, 4)

    @property
    def current_value(self) -> float:
        return round(self.quantity * self.current_price, 4)

    @property
    def profit_loss(self) -> float:
        return round(self.current_value - self.invested_amount, 4)

    @property
    def profit_loss_pct(self) -> float:
        if self.invested_amount == 0:
            return 0.0
        return round((self.profit_loss / self.invested_amount) * 100, 4)


# Create tables on startup (safe – does nothing if they already exist)
Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# DB dependency
# ---------------------------------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


# ---------------------------------------------------------------------------
# Helper – build response dict from ORM object
# ---------------------------------------------------------------------------

def _to_dict(p: Portfolio) -> dict:
    return {
        "id":               p.id,
        "ticker":           p.ticker,
        "market":           p.market,
        "quantity":         p.quantity,
        "average_cost":     p.average_cost,
        "current_price":    p.current_price,
        "status":           p.status,
        "notes":            p.notes,
        "created_at":       p.created_at,
        "updated_at":       p.updated_at,
        "invested_amount":  p.invested_amount,
        "current_value":    p.current_value,
        "profit_loss":      p.profit_loss,
        "profit_loss_pct":  p.profit_loss_pct,
    }


# ---------------------------------------------------------------------------
# GET /portfolio  – list all holdings
# ---------------------------------------------------------------------------

@router.get("/", summary="List all portfolio holdings")
def list_holdings(db: Session = Depends(get_db)):
    holdings = db.query(Portfolio).order_by(Portfolio.ticker).all()
    return [_to_dict(h) for h in holdings]


# ---------------------------------------------------------------------------
# POST /portfolio  – add a new holding
# ---------------------------------------------------------------------------

@router.post("/", status_code=status.HTTP_201_CREATED, summary="Add a new holding")
def add_holding(payload: dict, db: Session = Depends(get_db)):
    """
    Expected body:
      ticker, market, quantity, average_cost, current_price,
      status (optional, default "holding"), notes (optional)
    """
    ticker = str(payload.get("ticker", "")).upper().strip()
    if not ticker:
        raise HTTPException(status_code=422, detail="ticker is required")

    existing = db.query(Portfolio).filter(Portfolio.ticker == ticker).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Ticker '{ticker}' already exists. Use PATCH to update it."
        )

    try:
        holding = Portfolio(
            ticker=ticker,
            market=payload["market"],
            quantity=float(payload["quantity"]),
            average_cost=float(payload["average_cost"]),
            current_price=float(payload.get("current_price", 0.0)),
            status=payload.get("status", "holding"),
            notes=payload.get("notes"),
        )
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=f"Invalid payload: {exc}")

    db.add(holding)
    db.commit()
    db.refresh(holding)
    return _to_dict(holding)


# ---------------------------------------------------------------------------
# PATCH /portfolio/{ticker}  – edit an existing holding
# ---------------------------------------------------------------------------

@router.patch("/{ticker}", summary="Update a holding by ticker")
def update_holding(ticker: str, payload: dict, db: Session = Depends(get_db)):
    ticker = ticker.upper().strip()
    holding = db.query(Portfolio).filter(Portfolio.ticker == ticker).first()
    if not holding:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found")

    updatable = ("market", "quantity", "average_cost", "current_price", "status", "notes")
    for field in updatable:
        if field in payload and payload[field] is not None:
            value = payload[field]
            if field in ("quantity", "average_cost", "current_price"):
                value = float(value)
            setattr(holding, field, value)

    holding.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(holding)
    return _to_dict(holding)


# ---------------------------------------------------------------------------
# DELETE /portfolio/{ticker}  – remove a holding
# ---------------------------------------------------------------------------

@router.delete("/{ticker}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a holding")
def delete_holding(ticker: str, db: Session = Depends(get_db)):
    ticker = ticker.upper().strip()
    holding = db.query(Portfolio).filter(Portfolio.ticker == ticker).first()
    if not holding:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found")
    db.delete(holding)
    db.commit()
    return None


# ---------------------------------------------------------------------------
# GET /portfolio/summary  – aggregate stats
# ---------------------------------------------------------------------------

@router.get("/summary", summary="Portfolio-wide summary statistics")
def portfolio_summary(db: Session = Depends(get_db)):
    holdings = db.query(Portfolio).all()

    total_invested     = sum(h.invested_amount for h in holdings)
    total_value        = sum(h.current_value   for h in holdings)
    total_pl           = round(total_value - total_invested, 4)
    total_pl_pct       = (
        round((total_pl / total_invested) * 100, 4) if total_invested else 0.0
    )

    return {
        "total_invested":      round(total_invested, 4),
        "total_current_value": round(total_value, 4),
        "total_profit_loss":   total_pl,
        "total_profit_loss_pct": total_pl_pct,
        "holdings_count":      sum(1 for h in holdings if h.status == "holding"),
        "watching_count":      sum(1 for h in holdings if h.status == "watching"),
        "sold_count":          sum(1 for h in holdings if h.status == "sold"),
    }
