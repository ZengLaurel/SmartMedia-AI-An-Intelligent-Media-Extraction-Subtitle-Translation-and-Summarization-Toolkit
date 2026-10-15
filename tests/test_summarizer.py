"""Tests for summarizer.py — roadmap Phase 1, Step 5 (summary + keywords)."""

from summarizer import (
    extract_keywords,
    extract_main_points,
    extract_summary,
    save_summary_output,
)

SAMPLE_TEXT = (
    "Artificial intelligence is transforming the way people work and communicate. "
    "Machine learning models can now transcribe speech with high accuracy. "
    "Many companies are adopting AI tools to automate repetitive tasks. "
    "However, concerns about data privacy and job displacement remain significant. "
    "Researchers continue to study the long-term social impact of AI adoption. "
    "Despite the challenges, AI investment keeps growing across every industry."
)


def test_summary_generation():
    summary = extract_summary(SAMPLE_TEXT, num_sentences=3)

    assert isinstance(summary, str)
    assert len(summary) > 0
    assert summary != SAMPLE_TEXT


def test_summary_generation_short_text_returns_everything():
    short_text = "This is one sentence."
    summary = extract_summary(short_text, num_sentences=3)
    assert summary == "This is one sentence."


def test_keyword_extraction():
    keywords = extract_keywords(SAMPLE_TEXT, top_n=5)

    assert isinstance(keywords, list)
    assert len(keywords) > 0
    assert "ai" in keywords
    assert "the" not in keywords  # stopwords excluded


def test_main_points_extraction():
    points = extract_main_points(SAMPLE_TEXT, num_points=3)

    assert isinstance(points, list)
    assert len(points) == 3
    for point in points:
        assert isinstance(point, str)
        assert len(point) > 0


def test_summary_output_file(tmp_path):
    output_file = tmp_path / "summary.txt"

    result_path = save_summary_output(SAMPLE_TEXT, str(output_file))

    content = result_path.read_text(encoding="utf-8")
    assert "=== Summary ===" in content
    assert "=== Keywords ===" in content
    assert "=== Main Points ===" in content
    assert "ai" in content.lower()


def test_summary_empty_text():
    assert extract_summary("") == ""
    assert extract_keywords("") == []
    assert extract_main_points("") == []
