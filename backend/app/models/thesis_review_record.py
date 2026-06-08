from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, DateTime, Text, Enum, func
from ..database import Base
import enum

class ReviewStatus(enum.Enum):
    STRENGTHENING = "strengthening"
    WEAKENING = "weakening"
    INVALIDATED = "invalidated"
    ACTIVE = "active"

class ThesisReviewRecord(Base):
    __tablename__ = "thesis_reviews"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    position_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    timestamp: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[ReviewStatus] = mapped_column(Enum(ReviewStatus), nullable=False)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False)
    review_summary: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_points: Mapped[str] = mapped_column(Text, nullable=True)
    contradicting_points: Mapped[str] = mapped_column(Text, nullable=True)
