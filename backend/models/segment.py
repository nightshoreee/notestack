"""A classified chunk of a lecture: category (definition/example/formula/
key_concept/exam_tip), confidence_label (hedge detection), relevance_score
(syllabus similarity), and a generated Q/A pair. This is the row every
novel scoring signal in the system attaches to."""
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime
from sqlalchemy.sql import func
from database import Base


class Segment(Base):
    __tablename__ = "segments"

    id = Column(Integer, primary_key=True, index=True)
    lecture_id = Column(Integer, ForeignKey("lectures.id"), nullable=False)
    text = Column(Text, nullable=False)
    category = Column(String, nullable=False)
    confidence_label = Column(String, default="medium")   # high | medium | low
    relevance_score = Column(Float, default=0.0)            # 0-1 vs syllabus
    question = Column(Text, nullable=True)
    answer = Column(Text, nullable=True)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
