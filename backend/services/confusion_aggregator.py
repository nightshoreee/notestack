"""
Confusion aggregator \u2014 the peer-feedback novelty piece.
Collects "this is confusing" flags on a node within a course's shared study
room and turns that into a re-ranking signal: nodes flagged by more group
members are surfaced as higher-priority review items for the WHOLE group,
not just the person who flagged it.
"""
from sqlalchemy.orm import Session
from models import ConfusionFlag, Node


def flag_node_confusing(db: Session, node_id: int, user_id: int) -> ConfusionFlag:
    """Records a flag, but won't double-count the same student flagging the
    same node twice \u2014 returns the existing flag instead of creating a duplicate."""
    existing = (
        db.query(ConfusionFlag)
        .filter(ConfusionFlag.node_id == node_id, ConfusionFlag.user_id == user_id)
        .first()
    )
    if existing:
        return existing

    flag = ConfusionFlag(node_id=node_id, user_id=user_id)
    db.add(flag)
    db.commit()
    db.refresh(flag)
    return flag


def get_confusion_counts(db: Session, course_id: int) -> dict[int, int]:
    """Returns {node_id: number_of_students_who_flagged_it} for every node
    in a course \u2014 powers the '3/5 friends flagged this' UI badge."""
    node_ids = [n.id for n in db.query(Node).filter(Node.course_id == course_id).all()]
    counts = {}
    for node_id in node_ids:
        counts[node_id] = (
            db.query(ConfusionFlag).filter(ConfusionFlag.node_id == node_id).count()
        )
    return counts


def get_group_priority_review(db: Session, course_id: int, top_n: int = 5) -> list[int]:
    """Returns node_ids sorted by how many group members flagged them as
    confusing (most-flagged first) \u2014 powers the 'your group struggled with
    this' daily digest. Nodes with zero flags are excluded."""
    counts = get_confusion_counts(db, course_id)
    sorted_nodes = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    return [node_id for node_id, count in sorted_nodes if count > 0][:top_n]
