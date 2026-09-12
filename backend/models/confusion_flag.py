"""A student flagging a node as confusing inside a shared course study room.
Aggregated later to drive the group digest and review re-ranking."""
from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.sql import func
from database import Base


class ConfusionFlag(Base):
    __tablename__ = "confusion_flags"

    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
