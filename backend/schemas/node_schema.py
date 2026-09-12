"""Request/response shapes for roadmap nodes and answer submission."""
from pydantic import BaseModel
from typing import Optional


class NodeOut(BaseModel):
    id: int
    title: str
    difficulty: str
    position: int
    unit: int
    status: str            # merged in from this user's Progress row
    question: Optional[str] = None
    answer: Optional[str] = None
    category: Optional[str] = None

    class Config:
        from_attributes = True


class AnswerSubmit(BaseModel):
    node_id: int
    was_correct: bool


class ConfusionFlagIn(BaseModel):
    node_id: int
