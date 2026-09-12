"""Request/response shapes for course endpoints."""
from pydantic import BaseModel
from typing import Optional


class CourseCreate(BaseModel):
    name: str
    topics_to_study: Optional[str] = None
    syllabus_text: Optional[str] = None   # used later by the relevance scorer (Step 7)


class CourseOut(BaseModel):
    id: int
    name: str
    topics_to_study: Optional[str]
    invite_code: str

    class Config:
        from_attributes = True


class JoinCourse(BaseModel):
    invite_code: str
