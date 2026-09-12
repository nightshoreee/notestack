"""
Roadmap endpoints: fetch a course's node path (creating Progress rows lazily
for any nodes a student hasn't seen yet), submit an answer (now using real
spaced-repetition scheduling from Step 11), and list reviews due today.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Node, Progress, Segment, User
from schemas.node_schema import NodeOut, AnswerSubmit
from utils.auth_utils import get_current_user
from services.spaced_repetition import schedule_next_review, get_due_reviews

router = APIRouter(prefix="/roadmap", tags=["roadmap"])


def _ensure_progress_rows_exist(db: Session, user_id: int, course_id: int):
    """Lazily create Progress rows for any nodes the student hasn't seen yet.
    The first node in the course starts unlocked ('active'); the rest start 'locked'."""
    nodes = db.query(Node).filter(Node.course_id == course_id).order_by(Node.position).all()
    for i, node in enumerate(nodes):
        exists = (
            db.query(Progress)
            .filter(Progress.user_id == user_id, Progress.node_id == node.id)
            .first()
        )
        if not exists:
            status = "active" if i == 0 else "locked"
            db.add(Progress(user_id=user_id, node_id=node.id, status=status))
    db.commit()


@router.get("/{course_id}", response_model=list[NodeOut])
def get_roadmap(
    course_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    _ensure_progress_rows_exist(db, current_user.id, course_id)

    nodes = db.query(Node).filter(Node.course_id == course_id).order_by(Node.position).all()
    result = []
    for node in nodes:
        progress = (
            db.query(Progress)
            .filter(Progress.user_id == current_user.id, Progress.node_id == node.id)
            .first()
        )
        segment = db.query(Segment).filter(Segment.id == node.segment_id).first()
        result.append(
            NodeOut(
                id=node.id,
                title=node.title,
                difficulty=node.difficulty,
                position=node.position,
                unit=node.unit,
                status=progress.status if progress else "locked",
                question=segment.question if segment else None,
                answer=segment.answer if segment else None,
                category=segment.category if segment else None,
            )
        )
    return result


@router.post("/answer")
def submit_answer(
    payload: AnswerSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    node = db.query(Node).filter(Node.id == payload.node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    progress = (
        db.query(Progress)
        .filter(Progress.user_id == current_user.id, Progress.node_id == node.id)
        .first()
    )
    if not progress:
        raise HTTPException(status_code=404, detail="Progress not found — fetch roadmap first")

    # real spaced-repetition scheduling (Step 11) — replaces the simple status flip
    schedule_next_review(db, progress, node, payload.was_correct)

    # unlock the next node in position order if this one was answered correctly
    if payload.was_correct:
        next_node = (
            db.query(Node)
            .filter(Node.course_id == node.course_id, Node.position > node.position)
            .order_by(Node.position)
            .first()
        )
        if next_node:
            next_progress = (
                db.query(Progress)
                .filter(Progress.user_id == current_user.id, Progress.node_id == next_node.id)
                .first()
            )
            if next_progress and next_progress.status == "locked":
                next_progress.status = "active"
                db.commit()

    return {
        "ok": True,
        "new_status": progress.status,
        "next_review_at": progress.next_review_at,
        "interval_days": progress.interval_days,
    }


@router.get("/reviews/due")
def get_my_due_reviews(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Powers the daily engagement loop: nodes due for spaced-repetition review today."""
    due = get_due_reviews(db, current_user.id)
    return [
        {"node_id": p.node_id, "status": p.status, "next_review_at": p.next_review_at}
        for p in due
    ]
