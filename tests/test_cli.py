"""Tests for cli_main.py — roadmap Phase 2, Step 10 (formal CLI)."""

from unittest.mock import MagicMock, patch

import pytest

import cli_main
import pipeline
from downloader import InputValidationError


def test_cli_argument_parsing():
    parser = cli_main.build_parser()
    args = parser.parse_args(["--file", "video.mp4", "--source", "en", "--target", "zh"])

    assert args.file == "video.mp4"
    assert args.url is None
    assert args.source == "en"
    assert args.target == "zh"
    assert args.format == "srt"


def test_cli_argument_parsing_requires_file_or_url():
    parser = cli_main.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_cli_argument_parsing_rejects_both_file_and_url():
    parser = cli_main.build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--file", "a.mp4", "--url", "https://example.com/x"])


def test_cli_format_selection():
    parser = cli_main.build_parser()
    args = parser.parse_args(["--file", "video.mp4", "--format", "vtt"])
    assert args.format == "vtt"

    with pytest.raises(SystemExit):
        parser.parse_args(["--file", "video.mp4", "--format", "bogus"])


def _patch_pipeline(tmp_path, monkeypatch):
    monkeypatch.setattr(
        pipeline, "import_local_file", lambda path: tmp_path / "video.mp4"
    )
    monkeypatch.setattr(
        pipeline, "extract_audio", lambda src, dst: tmp_path / "audio.wav"
    )
    monkeypatch.setattr(pipeline, "get_audio_duration", lambda path: 10.0)
    monkeypatch.setattr(
        pipeline,
        "transcribe_audio",
        lambda path, language=None: {
            "language": "en",
            "segments": [{"start": 0.0, "end": 1.0, "text": "Hello world."}],
        },
    )
    monkeypatch.setattr(
        pipeline,
        "translate_segments",
        lambda segments, source, target: [
            {**seg, "translated_text": "你好世界。"} for seg in segments
        ],
    )
    monkeypatch.setattr(
        pipeline, "generate_srt", lambda segments, path: tmp_path / "subtitles.srt"
    )
    monkeypatch.setattr(
        pipeline, "generate_vtt", lambda segments, path: tmp_path / "subtitles.vtt"
    )
    monkeypatch.setattr(
        pipeline, "save_summary_output", lambda text, path: tmp_path / "summary.txt"
    )


def test_cli_prints_output_paths(tmp_path, monkeypatch, capsys):
    _patch_pipeline(tmp_path, monkeypatch)

    video_file = tmp_path / "video.mp4"
    video_file.write_bytes(b"fake")

    exit_code = cli_main.main(
        ["--file", str(video_file), "--output-dir", str(tmp_path)]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Pipeline completed successfully" in captured.out
    assert "audio.wav" in captured.out
    assert "subtitles.srt" in captured.out
    assert "summary.txt" in captured.out
    assert "processing.log" in captured.out
    assert (tmp_path / "processing.log").exists()


def test_cli_error_exit_code(tmp_path, monkeypatch, capsys):
    def raise_invalid(path):
        raise InputValidationError(f"File not found: {path}")

    monkeypatch.setattr(pipeline, "import_local_file", raise_invalid)

    exit_code = cli_main.main(
        ["--file", "does_not_exist.mp4", "--output-dir", str(tmp_path)]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Error:" in captured.err
    assert "Traceback" not in captured.err
    assert (tmp_path / "processing.log").exists()


def test_cli_requires_input():
    with pytest.raises(SystemExit):
        cli_main.main([])
