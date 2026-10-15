"""Text summarization and keyword extraction.

Uses a lightweight, dependency-free extractive approach (word-frequency
weighted sentence scoring, i.e. a simplified TextRank) rather than a remote
LLM, so this module runs fully offline and is trivially unit-testable
without mocking any external service (NFR-06).
"""

import re
from collections import Counter
from pathlib import Path

_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "of", "to", "in", "on", "for",
    "with", "as", "is", "are", "was", "were", "be", "been", "being", "it",
    "its", "this", "that", "these", "those", "at", "by", "from", "they",
    "them", "their", "he", "she", "his", "her", "we", "our", "you", "your",
    "i", "my", "not", "no", "do", "does", "did", "have", "has", "had", "will",
    "would", "can", "could", "should", "may", "might", "than", "then", "so",
    "because", "which", "who", "what", "when", "where", "how",
}

_WORD_RE = re.compile(r"[A-Za-z']+|[一-鿿]")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?。！？])\s+")


def _split_sentences(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    sentences = [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]
    return sentences


def _tokenize(text: str) -> list[str]:
    return [w.lower() for w in _WORD_RE.findall(text) if w.lower() not in _STOPWORDS]


def extract_keywords(text: str, top_n: int = 10) -> list[str]:
    """Return the top_n most frequent non-stopword tokens in text (FR-23)."""
    words = _tokenize(text)
    counts = Counter(words)
    return [word for word, _ in counts.most_common(top_n)]


def _score_sentences(sentences: list[str]) -> list[float]:
    tokenized = [set(_tokenize(s)) for s in sentences]

    def overlap(a: set, b: set) -> float:
        if not a or not b:
            return 0.0
        return len(a & b) / (len(a) + len(b))

    scores = [0.0] * len(sentences)
    for i in range(len(sentences)):
        for j in range(len(sentences)):
            if i != j:
                scores[i] += overlap(tokenized[i], tokenized[j])
    return scores


def extract_summary(text: str, num_sentences: int = 3) -> str:
    """Return a concise extractive summary of text (FR-22).

    Picks the num_sentences highest-scoring sentences (by shared-word
    overlap with the rest of the text) and joins them in original order.
    """
    sentences = _split_sentences(text)
    if not sentences:
        return ""
    if len(sentences) <= num_sentences:
        return " ".join(sentences)

    scores = _score_sentences(sentences)
    ranked_indices = sorted(range(len(sentences)), key=lambda i: scores[i], reverse=True)
    top_indices = sorted(ranked_indices[:num_sentences])
    return " ".join(sentences[i] for i in top_indices)


def extract_main_points(text: str, num_points: int = 5) -> list[str]:
    """Return the top-ranked sentences as a structured list of main points,
    distinct from the free-text summary (FR-24).
    """
    sentences = _split_sentences(text)
    if not sentences:
        return []
    if len(sentences) <= num_points:
        return sentences

    scores = _score_sentences(sentences)
    ranked_indices = sorted(range(len(sentences)), key=lambda i: scores[i], reverse=True)
    top_indices = sorted(ranked_indices[:num_points])
    return [sentences[i] for i in top_indices]


def save_summary_output(text: str, output_path: str) -> Path:
    """Generate summary/keywords/main points from text and write them to a
    plain-text output file (FR-25).
    """
    summary = extract_summary(text)
    keywords = extract_keywords(text)
    main_points = extract_main_points(text)

    lines = [
        "=== Summary ===",
        summary,
        "",
        "=== Keywords ===",
        ", ".join(keywords),
        "",
        "=== Main Points ===",
    ]
    lines.extend(f"- {point}" for point in main_points)

    path = Path(output_path)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path

