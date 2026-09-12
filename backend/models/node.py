"""A single roadmap node (one Duolingo-style step), built from exactly one
Segment. position determines path order; difficulty is derived from the
segment's confidence_label."""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from database import Base


class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    segment_id = Column(Integer, ForeignKey("segments.id"), nullable=False)
    title = Column(String, nullable=False)
    difficulty = Column(String, default="medium")    # easy | medium | hard
    position = Column(Integer, nullable=False)
    unit = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
