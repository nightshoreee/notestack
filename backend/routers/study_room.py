"""
Study room endpoints \u2014 the collaborative layer. Friends who joined a course
via its invite code (Step 4) land here: flag nodes as confusing, see how many
group members flagged each node, get a daily digest of what the group
struggled with, and see group-wide completion per node.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import User, Node, Progress
from schemas.node_schema import ConfusionFlagIn
from utils.auth_utils import get_current_user
from services.confusion_aggregator import (
    flag_node_confusing,
    get_confusion_counts,
    get_group_priority_review,
)

router = APIRouter(prefix="/study-room", tags=["study-room"])


@router.post("/flag")
def flag_confusing(
    payload: ConfusionFlagIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    flag_node_confusing(db, node_id=payload.node_id, user_id=current_user.id)
    return {"ok": True}


@router.get("/{course_id}/confusion-counts")
def confusion_counts(
    course_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """'3/5 friends flagged this node' style data for the roadmap UI."""
    return get_confusion_counts(db, course_id)


@router.get("/{course_id}/digest")
def daily_digest(
    course_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """'Here's what your group struggled with' \u2014 top confusing nodes across the group."""
    priority_node_ids = get_group_priority_review(db, course_id)
    nodes = db.query(Node).filter(Node.id.in_(priority_node_ids)).all()
    # preserve the priority order from get_group_priority_review, not DB insertion order
    nodes_by_id = {n.id: n for n in nodes}
    ordered = [nodes_by_id[nid] for nid in priority_node_ids if nid in nodes_by_id]
    return [{"node_id": n.id, "title": n.title} for n in ordered]


@router.get("/{course_id}/group-progress")
def group_progress(
    course_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """Completion state per node across everyone who has progress on this course's nodes."""
    node_ids = [n.id for n in db.query(Node).filter(Node.course_id == course_id).all()]
    result = {}
    for node_id in node_ids:
        completed = (
            db.query(Progress)
            .filter(Progress.node_id == node_id, Progress.status == "completed")
            .count()
        )
        total = db.query(Progress).filter(Progress.node_id == node_id).count()
        result[node_id] = {"completed": completed, "total": total}
    return result
