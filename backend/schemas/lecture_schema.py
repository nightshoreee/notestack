"""Request/response shapes for lecture upload and its resulting segments."""
from pydantic import BaseModel
from typing import Optional


class LectureOut(BaseModel):
    id: int
    title: str
    source_type: str
    status: str

    class Config:
        from_attributes = True


class SegmentOut(BaseModel):
    id: int
    text: str
    category: str
    confidence_label: str
    relevance_score: float
    question: Optional[str]
    answer: Optional[str]

    class Config:
        from_attributes = True
