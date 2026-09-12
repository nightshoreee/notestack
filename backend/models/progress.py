"""Per-student progress on a single node, plus spaced-repetition scheduling
fields (simplified SM-2 style: ease_factor, interval_days, next_review_at)."""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from database import Base


class Progress(Base):
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    status = Column(String, default="locked")   # locked | active | completed | needs_review
    correct_streak = Column(Integer, default=0)
    ease_factor = Column(Integer, default=250)    # SM-2 style ease, stored *100
    interval_days = Column(Integer, default=1)
    next_review_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
