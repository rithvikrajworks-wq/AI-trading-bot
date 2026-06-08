from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Float, Integer, Enum, Text, func
from ..database import Base
import enum

class OutcomeStatus(enum.Enum):
    WINNER = "WINNER"
    LOSER = "LOSER"
    NEUTRAL = "NEUTRAL"

class PositionOutcome(Base):
    __tablename__ = "position_outcomes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    position_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    current_price: Mapped[float] = mapped_column(Float, nullable=False)
    realized_return: Mapped[float] = mapped_column(Float, nullable=True)
    unrealized_return: Mapped[float] = mapped_column(Float, nullable=True)
    holding_period_days: Mapped[int] = mapped_column(Integer, nullable=True)
    outcome_status: Mapped[OutcomeStatus] = mapped_column(Enum(OutcomeStatus), nullable=False)
