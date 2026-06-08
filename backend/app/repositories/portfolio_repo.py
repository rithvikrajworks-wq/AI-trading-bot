from sqlalchemy.orm import Session
from ..models.portfolio_position import PortfolioPosition, PositionStatus

def add_position(db: Session, user_id: str, ticker: str, quantity: float, average_cost: float, thesis: str = None, conviction_level: str = None, notes: str = None, status: PositionStatus = PositionStatus.WATCHING) -> PortfolioPosition:
    """Create a new portfolio position for a user."""
    position = PortfolioPosition(
        user_id=user_id,
        ticker=ticker,
        quantity=quantity,
        average_cost=average_cost,
        thesis=thesis,
        conviction_level=conviction_level,
        notes=notes,
        status=status,
    )
    db.add(position)
    db.commit()
    db.refresh(position)
    return position

def update_position(db: Session, user_id: str, ticker: str, **updates) -> PortfolioPosition | None:
    """Update fields of an existing position. Returns the updated record or None if not found."""
    position = db.query(PortfolioPosition).filter(PortfolioPosition.user_id == user_id, PortfolioPosition.ticker == ticker).first()
    if not position:
        return None
    for field, value in updates.items():
        if hasattr(position, field):
            setattr(position, field, value)
    db.commit()
    db.refresh(position)
    return position

def remove_position(db: Session, user_id: str, ticker: str) -> bool:
    """Delete a position. Returns True if a row was deleted."""
    result = db.query(PortfolioPosition).filter(PortfolioPosition.user_id == user_id, PortfolioPosition.ticker == ticker).delete()
    db.commit()
    return result > 0

def get_position(db: Session, user_id: str, ticker: str) -> PortfolioPosition | None:
    return db.query(PortfolioPosition).filter(PortfolioPosition.user_id == user_id, PortfolioPosition.ticker == ticker).first()

def get_all_positions(db: Session, user_id: str) -> list[PortfolioPosition]:
    return db.query(PortfolioPosition).filter(PortfolioPosition.user_id == user_id).all()

def get_watchlist(db: Session, user_id: str) -> list[PortfolioPosition]:
    return (
        db.query(PortfolioPosition)
        .filter(PortfolioPosition.user_id == user_id, PortfolioPosition.status == PositionStatus.WATCHING)
        .all()
    )
