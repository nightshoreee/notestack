"""
Spaced repetition scheduling \u2014 a simplified SM-2-style algorithm, WEIGHTED by
the node's difficulty (which comes from the Segment's confidence_label). A node
the professor was "low confidence" (hedged) about gets a SHORTER review interval
even after a correct answer, since surface-level correctness on uncertain
content is less trustworthy than correctness on clearly-stated material.

This is what Step 10's simple status-flip logic gets replaced with.
"""
import math
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import Progress, Node

# hard/low-confidence nodes resurface sooner even when answered correctly;
# easy/high-confidence nodes get to stretch their review interval further
DIFFICULTY_INTERVAL_MULTIPLIER = {
    "easy": 1.3,
    "medium": 1.0,
    "hard": 0.6,
}


def schedule_next_review(db: Session, progress: Progress, node: Node, was_correct: bool) -> Progress:
    """Updates a Progress row's ease_factor, interval_days, next_review_at, and
    status based on whether the student answered correctly, taking the node's
    difficulty into account. Mutates and commits progress; returns it refreshed."""
    multiplier = DIFFICULTY_INTERVAL_MULTIPLIER.get(node.difficulty, 1.0)

    if was_correct:
        progress.correct_streak += 1
        progress.ease_factor = min(400, progress.ease_factor + 10)
        base_interval = max(1, progress.interval_days) * (progress.ease_factor / 250)
        # math.ceil (not round): on the very first review, base_interval*multiplier is
        # often < 1.5 for every difficulty band, and round() collapses easy/medium/hard
        # to the same interval_days=1 -- silently erasing the difficulty signal exactly
        # when it matters most (the first time a student sees this node). ceil keeps a
        # low-confidence "hard" node's shorter interval visibly distinct from an easy one.
        progress.interval_days = max(1, math.ceil(base_interval * multiplier))
        progress.status = "completed"
    else:
        progress.correct_streak = 0
        progress.ease_factor = max(130, progress.ease_factor - 20)
        progress.interval_days = 1  # wrong answer -> resurface tomorrow regardless of difficulty
        progress.status = "needs_review"

    progress.next_review_at = datetime.utcnow() + timedelta(days=progress.interval_days)
    if was_correct:
        progress.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(progress)
    return progress


def get_due_reviews(db: Session, user_id: int) -> list[Progress]:
    """Returns every Progress row for this user whose next_review_at has arrived
    or passed \u2014 this powers the daily engagement loop (Step 1's original design goal)."""
    now = datetime.utcnow()
    return (
        db.query(Progress)
        .filter(Progress.user_id == user_id)
        .filter(Progress.next_review_at.isnot(None))
        .filter(Progress.next_review_at <= now)
        .all()
    )
