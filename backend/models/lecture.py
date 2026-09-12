"""A single uploaded lecture transcript or PDF, tied to a course."""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from database import Base


class Lecture(Base):
    __tablename__ = "lectures"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    title = Column(String, nullable=False)
    source_type = Column(String, nullable=False)     # "transcript" | "pdf"
    raw_text = Column(Text, nullable=False)
    status = Column(String, default="processing")     # processing | ready | failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
