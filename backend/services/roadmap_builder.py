"""
Roadmap builder — converts classified + confidence-tagged + relevance-scored
segments into an ORDERED list of roadmap nodes. This ordering logic is the
actual novel contribution, not the Duolingo-style UI itself:

  1. Segments are sorted by relevance_score DESC first -> exam-relevant
     material comes earlier in the path, so students hit high-value content
     sooner instead of wading through generic content first.
  2. Within similar relevance, "low" confidence_label segments (professor
     hedged / was uncertain) are pushed slightly later and marked "hard"
     difficulty, since they need more scaffolding before a student is ready.
  3. definition/key_concept categories are nudged earlier than example/
     exam_tip within the same relevance+confidence band, so foundational
     material precedes applied material.
"""
from sqlalchemy.orm import Session
from models import Segment, Node

CATEGORY_WEIGHT = {
    "definition": 0,
    "key_concept": 1,
    "formula": 2,
    "example": 3,
    "exam_tip": 4,
}

CONFIDENCE_DIFFICULTY = {
    "high": "easy",
    "medium": "medium",
    "low": "hard",
}

CONFIDENCE_PENALTY = {"high": 0, "medium": 0.5, "low": 1}


def _sort_key(segment: Segment):
    relevance_rank = -segment.relevance_score   # negate: higher relevance sorts first
    confidence_penalty = CONFIDENCE_PENALTY.get(segment.confidence_label, 0.5)
    category_rank = CATEGORY_WEIGHT.get(segment.category, 5)
    return (relevance_rank, confidence_penalty, category_rank)


def build_roadmap(db: Session, course_id: int, segments: list[Segment], unit: int = 1) -> list[Node]:
    """Takes classified segments for one lecture and creates ordered Node rows
    for the course, continuing numbering after any nodes that already exist."""
    ordered_segments = sorted(segments, key=_sort_key)

    existing_count = db.query(Node).filter(Node.course_id == course_id).count()

    nodes = []
    for i, seg in enumerate(ordered_segments):
        node = Node(
            course_id=course_id,
            segment_id=seg.id,
            title=seg.text[:60] + ("..." if len(seg.text) > 60 else ""),
            difficulty=CONFIDENCE_DIFFICULTY.get(seg.confidence_label, "medium"),
            position=existing_count + i,
            unit=unit,
        )
        db.add(node)
        nodes.append(node)

    db.commit()
    for n in nodes:
        db.refresh(n)
    return nodes
