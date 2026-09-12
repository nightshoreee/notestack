"""
Course endpoints: create, list-mine, get-by-id, and join-by-invite-code
(the mechanism friends use to land in the same shared study room later).
"""
import secrets
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Course, User
from schemas.course_schema import CourseCreate, CourseOut, JoinCourse
from utils.auth_utils import get_current_user

router = APIRouter(prefix="/courses", tags=["courses"])


@router.post("", response_model=CourseOut)
def create_course(
    payload: CourseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = Course(
        owner_id=current_user.id,
        name=payload.name,
        topics_to_study=payload.topics_to_study,
        syllabus_text=payload.syllabus_text,
        invite_code=secrets.token_hex(4),   # short shareable code, e.g. "a1b2c3d4"
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.get("", response_model=list[CourseOut])
def list_my_courses(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return db.query(Course).filter(Course.owner_id == current_user.id).all()


@router.get("/{course_id}", response_model=CourseOut)
def get_course(
    course_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.post("/join", response_model=CourseOut)
def join_course(
    payload: JoinCourse,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Friend joins an existing course's shared study room via invite code."""
    course = db.query(Course).filter(Course.invite_code == payload.invite_code).first()
    if not course:
        raise HTTPException(status_code=404, detail="Invalid invite code")
    return course
