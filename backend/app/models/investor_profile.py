from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, Text, Integer, JSON, func
from ..database import Base

class InvestorProfile(Base):
    __tablename__ = "investor_profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    profile_version: Mapped[int] = mapped_column(Integer, nullable=False)
    generated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    investor_style: Mapped[str] = mapped_column(String(50), nullable=True)
    risk_tolerance: Mapped[str] = mapped_column(String(20), nullable=True)
    conviction_style: Mapped[str] = mapped_column(String(20), nullable=True)
    holding_period_preference: Mapped[str] = mapped_column(String(20), nullable=True)
    preferred_sectors: Mapped[Text] = mapped_column(Text, nullable=True)  # JSON string list
    preferred_market_caps: Mapped[Text] = mapped_column(Text, nullable=True)  # JSON string list
    strongest_strengths: Mapped[Text] = mapped_column(Text, nullable=True)  # JSON string list
    recurring_mistakes: Mapped[Text] = mapped_column(Text, nullable=True)  # JSON string list
    behavior_summary: Mapped[Text] = mapped_column(Text, nullable=True)
    profile_confidence: Mapped[int] = mapped_column(Integer, nullable=True)
    raw_profile_json: Mapped[Text] = mapped_column(Text, nullable=False)
