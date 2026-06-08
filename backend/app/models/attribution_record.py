from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, Text, Enum, DateTime, func
from ..database import Base
import enum

class AttributionRecord(Base):
    __tablename__ = "attribution_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    position_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    analysis_id: Mapped[int] = mapped_column(Integer, nullable=False)
    thesis_version: Mapped[int] = mapped_column(Integer, nullable=False)
    journal_entry_id: Mapped[int] = mapped_column(Integer, nullable=False)
    thesis_accuracy: Mapped[str] = mapped_column(Text, nullable=True)
    analysis_accuracy: Mapped[str] = mapped_column(Text, nullable=True)
    execution_accuracy: Mapped[str] = mapped_column(Text, nullable=True)
    attribution_summary: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
