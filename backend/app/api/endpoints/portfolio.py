from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database import get_db
from ...repositories import portfolio_repo
from ...schemas import portfolio as portfolio_schema

router = APIRouter(prefix="/portfolio", tags=["portfolio"])

# List all holdings for a user (placeholder user_id)
@router.get("/", summary="List all portfolio holdings")
def list_holdings(user_id: str = "default_user", db: Session = Depends(get_db)):
    positions = portfolio_repo.get_all_positions(db, user_id)
    return [portfolio_schema.PortfolioResponse.from_orm(p) for p in positions]

# Add a new holding
@router.post("/", status_code=status.HTTP_201_CREATED, summary="Add a new holding")
def add_holding(payload: portfolio_schema.PortfolioCreate, user_id: str = "default_user", db: Session = Depends(get_db)):
    existing = portfolio_repo.get_position(db, user_id, payload.ticker.upper())
    if existing:
        raise HTTPException(status_code=409, detail=f"Ticker '{payload.ticker}' already exists for this user.")
    position = portfolio_repo.add_position(
        db,
        user_id=user_id,
        ticker=payload.ticker.upper(),
        quantity=payload.quantity,
        average_cost=payload.average_cost,
        thesis=None,
        conviction_level=None,
        notes=payload.notes,
        status=portfolio_repo.PositionStatus.WATCHING if payload.status == "watching" else portfolio_repo.PositionStatus.HOLDING,
    )
    return portfolio_schema.PortfolioResponse.from_orm(position)

# Update a holding
@router.patch("/{ticker}", summary="Update a holding by ticker")
def update_holding(ticker: str, payload: portfolio_schema.PortfolioUpdate, user_id: str = "default_user", db: Session = Depends(get_db)):
    updates = payload.dict(exclude_unset=True)
    if "status" in updates:
        updates["status"] = (
            portfolio_repo.PositionStatus.WATCHING
            if updates["status"] == "watching"
            else portfolio_repo.PositionStatus.HOLDING
        )
    position = portfolio_repo.update_position(db, user_id, ticker.upper(), **updates)
    if not position:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found for this user.")
    return portfolio_schema.PortfolioResponse.from_orm(position)

# Delete a holding
@router.delete("/{ticker}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a holding")
def delete_holding(ticker: str, user_id: str = "default_user", db: Session = Depends(get_db)):
    success = portfolio_repo.remove_position(db, user_id, ticker.upper())
    if not success:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found for this user.")
    return None

# Portfolio summary
@router.get("/summary", summary="Portfolio-wide summary statistics")
def portfolio_summary(user_id: str = "default_user", db: Session = Depends(get_db)):
    positions = portfolio_repo.get_all_positions(db, user_id)
    total_invested = sum(p.quantity * p.average_cost for p in positions)
    total_value = sum(p.quantity * p.current_price for p in positions)
    total_pl = round(total_value - total_invested, 4)
    total_pl_pct = round((total_pl / total_invested) * 100, 4) if total_invested else 0.0
    holdings_count = sum(1 for p in positions if p.status.name.lower() in ("active", "holding"))
    watching_count = sum(1 for p in positions if p.status == portfolio_repo.PositionStatus.WATCHING)
    sold_count = sum(1 for p in positions if p.status == portfolio_repo.PositionStatus.SOLD)
    return portfolio_schema.PortfolioSummary(
        total_invested=round(total_invested, 4),
        total_current_value=round(total_value, 4),
        total_profit_loss=total_pl,
        total_profit_loss_pct=total_pl_pct,
        holdings_count=holdings_count,
        watching_count=watching_count,
        sold_count=sold_count,
    )
