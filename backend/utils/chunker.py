"""
Splits raw lecture/PDF text into paragraph-sized chunks for the AI classifier
(Step 6) to process one at a time. Keeps each chunk under ~max_words so a
single Gemini call can handle it without losing focus on one idea.
"""
import re


def chunk_text(raw_text: str, max_words: int = 60) -> list[str]:
    raw_text = re.sub(r"\s+", " ", raw_text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", raw_text)

    chunks = []
    current = []
    word_count = 0

    for sentence in sentences:
        words_in_sentence = len(sentence.split())
        if word_count + words_in_sentence > max_words and current:
            chunks.append(" ".join(current))
            current = []
            word_count = 0
        current.append(sentence)
        word_count += words_in_sentence

    if current:
        chunks.append(" ".join(current))

    return [c for c in chunks if c.strip()]
