"""
Syllabus-anchored relevance scoring (the core novelty piece).
Embeds the course syllabus + each lecture chunk locally with
sentence-transformers (free, no API key, runs on your own machine) and
scores each chunk by cosine similarity to the syllabus text. A higher
score means the chunk is more likely to matter for THIS specific course,
rather than a generic "importance" label.
"""
from sentence_transformers import SentenceTransformer, util

_embedder = None  # lazy-loaded: no need to download/load the model for
                    # courses with no syllabus text, and it keeps app startup fast


def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")  # small, fast, free, local
    return _embedder


def score_relevance(chunks: list[str], syllabus_text: str) -> list[float]:
    """Returns a 0-1 relevance score per chunk, relative to the syllabus text.
    If no syllabus was provided, every chunk gets a neutral 0.5 score so the
    roadmap builder (Step 9) doesn't wrongly treat everything as irrelevant —
    and the embedding model never even has to load in that case."""
    if not chunks:
        return []

    if not syllabus_text or not syllabus_text.strip():
        return [0.5 for _ in chunks]

    embedder = _get_embedder()
    syllabus_embedding = embedder.encode(syllabus_text, convert_to_tensor=True)
    chunk_embeddings = embedder.encode(chunks, convert_to_tensor=True)

    scores = util.cos_sim(chunk_embeddings, syllabus_embedding).squeeze(1).tolist()
    # normalize defensively into 0-1 (cosine similarity can dip slightly negative)
    return [max(0.0, min(1.0, (s + 1) / 2)) for s in scores]

