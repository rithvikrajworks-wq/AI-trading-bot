from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Text, Enum, Integer, func
from ..database import Base
import enum

class ThesisSource(enum.Enum):
    ORIGINAL_PURCHASE = "original_purchase"
    MANUAL_UPDATE = "manual_update"
    AI_REVIEW = "ai_review"

class ThesisStatus(enum.Enum):
    ACTIVE = "active"
    STRENGTHENING = "strengthening"
    WEAKENING = "weakening"
    INVALIDATED = "invalidated"

class ThesisRecord(Base):
    __tablename__ = "thesis_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    position_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    timestamp: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    thesis_text: Mapped[str] = mapped_column(Text, nullable=False)
    thesis_version: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[ThesisSource] = mapped_column(Enum(ThesisSource), nullable=False)
    status: Mapped[ThesisStatus] = mapped_column(Enum(ThesisStatus), nullable=False, default=ThesisStatus.ACTIVE)

    __table_args__ = (
        # Ensure no duplicate version per position
        # Unique constraint (position_id, thesis_version)
        # SQLite syntax handled by SQLAlchemy
        {'sqlite_autoincrement': True},
    )
