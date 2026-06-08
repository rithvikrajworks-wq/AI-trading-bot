from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Enum, Float, Integer, Text, func
from ..database import Base
import enum

class TradeAction(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    WATCH = "WATCH"

class TradeJournalEntry(Base):
    __tablename__ = "trade_journal"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    timestamp: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    action: Mapped[TradeAction] = mapped_column(Enum(TradeAction), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    execution_price: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    conviction_level: Mapped[str] = mapped_column(String(20), nullable=True)
    linked_position_id: Mapped[int] = mapped_column(Integer, nullable=True)
    linked_analysis_id: Mapped[int] = mapped_column(Integer, nullable=True)
    linked_thesis_version: Mapped[int] = mapped_column(Integer, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
