"""
Lecture upload endpoint — the full pipeline in one call:
upload -> extract text -> chunk (Step 5) -> classify+hedge-tag+Q/A via AI (Step 6)
-> relevance score vs syllabus (Step 7) -> save segments -> build roadmap nodes (Step 9)
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from database import get_db
from models import Lecture, Segment, Course, User
from schemas.lecture_schema import LectureOut, SegmentOut
from utils.auth_utils import get_current_user
from utils.pdf_parser import extract_text_from_pdf
from utils.chunker import chunk_text
from services.ai_service import analyze_chunks_batch
from services.relevance_service import score_relevance
from services.roadmap_builder import build_roadmap

router = APIRouter(prefix="/lectures", tags=["lectures"])


@router.post("/upload", response_model=LectureOut)
async def upload_lecture(
    course_id: int = Form(...),
    title: str = Form(...),
    source_type: str = Form(...),           # "transcript" | "pdf"
    transcript_text: str = Form(None),        # used when source_type == "transcript"
    file: UploadFile = File(None),            # used when source_type == "pdf"
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # 1. get raw text depending on source type
    if source_type == "pdf":
        if not file:
            raise HTTPException(status_code=400, detail="PDF file is required")
        file_bytes = await file.read()
        raw_text = extract_text_from_pdf(file_bytes)
    else:
        if not transcript_text:
            raise HTTPException(status_code=400, detail="transcript_text is required")
        raw_text = transcript_text

    if not raw_text.strip():
        raise HTTPException(status_code=400, detail="Could not extract any text from upload")

    lecture = Lecture(
        course_id=course_id, title=title, source_type=source_type,
        raw_text=raw_text, status="processing",
    )
    db.add(lecture)
    db.commit()
    db.refresh(lecture)

    # 2. chunk
    chunks = chunk_text(raw_text)

    # 3. AI: classify + hedge-tag + generate Q/A (one batched Gemini call per chunk)
    analyzed = analyze_chunks_batch(chunks)

    # 4. relevance score each chunk against the course syllabus (local embeddings, free)
    relevance_scores = score_relevance(chunks, course.syllabus_text or "")

    # 5. persist segments
    segments = []
    for i, (chunk, analysis, rel_score) in enumerate(zip(chunks, analyzed, relevance_scores)):
        segment = Segment(
            lecture_id=lecture.id,
            text=chunk,
            category=analysis["category"],
            confidence_label=analysis["confidence_label"],
            relevance_score=rel_score,
            question=analysis["question"],
            answer=analysis["answer"],
            order_index=i,
        )
        db.add(segment)
        segments.append(segment)

    db.commit()
    for s in segments:
        db.refresh(s)

    # 6. build roadmap nodes from these segments (Step 9's ordering logic)
    build_roadmap(db, course_id=course_id, segments=segments, unit=1)

    lecture.status = "ready"
    db.commit()
    db.refresh(lecture)
    return lecture


@router.get("/{lecture_id}/segments", response_model=list[SegmentOut])
def get_lecture_segments(
    lecture_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return db.query(Segment).filter(Segment.lecture_id == lecture_id).order_by(Segment.order_index).all()


@router.get("/course/{course_id}", response_model=list[LectureOut])
def list_course_lectures(
    course_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return db.query(Lecture).filter(Lecture.course_id == course_id).all()
