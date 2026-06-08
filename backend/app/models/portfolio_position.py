from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Integer, Float, Text, Enum, func
from ..database import Base
import enum

class PositionStatus(enum.Enum):
    ACTIVE = "active"
    SOLD = "sold"
    WATCHING = "watching"

class PortfolioPosition(Base):
    __tablename__ = "portfolio_positions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    average_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    first_added_date: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    thesis: Mapped[str] = mapped_column(Text, nullable=True)
    conviction_level: Mapped[str] = mapped_column(String(20), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    last_reviewed: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[PositionStatus] = mapped_column(Enum(PositionStatus), nullable=False, default=PositionStatus.WATCHING)
