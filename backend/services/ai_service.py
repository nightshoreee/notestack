"""
Core AI layer. Calls Gemini once per chunk with a single batched prompt that
returns category classification + hedge/confidence detection + a generated
Q/A pair, all in one JSON response. Batching these three things into ONE
prompt per chunk (instead of three separate calls) keeps API usage — and
free-tier quota — low.

Uses the current `google-genai` SDK (the older `google-generativeai` package
is deprecated as of this writing).
"""
import json
from google import genai
from config import settings

_client = None  # lazy-loaded: prevents the whole app from crashing on startup if
                 # GEMINI_API_KEY isn't set yet — the error only surfaces when a
                 # chunk is actually analyzed, and analyze_chunk already catches it
_MODEL_NAME = "gemini-1.5-flash"


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client

SYSTEM_PROMPT = """You are an assistant that analyzes a single chunk of a lecture transcript or
textbook excerpt for a study app. Return ONLY valid JSON, no markdown fences, no preamble.

Classify the chunk and return this exact JSON shape:
{
  "category": "definition" | "example" | "formula" | "key_concept" | "exam_tip",
  "confidence_label": "high" | "medium" | "low",
  "question": "a short study question testing this chunk's content",
  "answer": "a concise correct answer to that question"
}

Rules for confidence_label (this reflects how CERTAIN the speaker/text sounds, not how
important the content is):
- "low": text uses hedging language ("I think", "roughly", "probably", "not 100% sure",
  "something like", self-corrections)
- "high": text uses definitive or emphasized language ("this WILL be on the exam",
  "remember this", "the definition is exactly", "always", "must")
- "medium": neutral, plainly stated factual content with no strong signal either way

If the chunk doesn't clearly fit definition/example/formula/exam_tip, use "key_concept".
"""

VALID_CATEGORIES = {"definition", "example", "formula", "key_concept", "exam_tip"}
VALID_CONFIDENCE = {"high", "medium", "low"}


def _parse_ai_response(raw_text: str) -> dict:
    """Parses and validates the model's JSON output. Raises on anything unusable
    so the caller can fall back to safe defaults instead of trusting bad data."""
    cleaned = raw_text.strip().replace("```json", "").replace("```", "").strip()
    data = json.loads(cleaned)

    category = data.get("category", "key_concept")
    confidence_label = data.get("confidence_label", "medium")

    return {
        "category": category if category in VALID_CATEGORIES else "key_concept",
        "confidence_label": confidence_label if confidence_label in VALID_CONFIDENCE else "medium",
        "question": data.get("question", "") or "",
        "answer": data.get("answer", "") or "",
    }


def analyze_chunk(chunk_text: str) -> dict:
    """Single Gemini call per chunk. Returns a dict matching the shape above.
    Falls back to safe defaults if the model call fails or returns malformed JSON,
    so one bad chunk never crashes the whole lecture upload."""
    prompt = f"{SYSTEM_PROMPT}\n\nChunk:\n\"\"\"\n{chunk_text}\n\"\"\""
    try:
        client = _get_client()
        response = client.models.generate_content(model=_MODEL_NAME, contents=prompt)
        return _parse_ai_response(response.text)
    except Exception:
        return {
            "category": "key_concept",
            "confidence_label": "medium",
            "question": "",
            "answer": "",
        }


def analyze_chunks_batch(chunks: list[str]) -> list[dict]:
    """Runs analyze_chunk over a list of chunks. Simple loop for MVP clarity —
    swap for asyncio.gather + async Gemini calls later if upload speed matters."""
    return [analyze_chunk(c) for c in chunks]
