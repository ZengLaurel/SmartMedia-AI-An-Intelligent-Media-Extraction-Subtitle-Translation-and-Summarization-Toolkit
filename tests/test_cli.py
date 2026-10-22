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
    # The source group is now required=False (batch mode is a third option),
    # so the emptiness check happens in main(), not at parse time.
    with pytest.raises(SystemExit):
        cli_main.main([])


def test_cli_argument_parsing_download_urls():
    parser = cli_main.build_parser()
    args = parser.parse_args(
        ["--download-urls", "https://example.com/a", "https://example.com/b",
         "--max-concurrent-downloads", "4"]
    )
    assert args.download_urls == ["https://example.com/a", "https://example.com/b"]
    assert args.max_concurrent_downloads == 4


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


def test_cli_batch_download_success(tmp_path, monkeypatch, capsys):
    from downloader import BatchDownloadResult

    monkeypatch.setattr(
        cli_main,
        "download_multiple_from_urls",
        lambda urls, output_dir, max_workers, on_progress=None, cancel_event=None: [
            BatchDownloadResult(index=i, url=u, path=tmp_path / f"{i}.mp4")
            for i, u in enumerate(urls)
        ],
    )

    exit_code = cli_main.main(
        ["--download-urls", "https://example.com/a", "https://example.com/b",
         "--output-dir", str(tmp_path)]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Downloaded:" in captured.out
    assert (tmp_path / "processing.log").exists()
    log = (tmp_path / "processing.log").read_text(encoding="utf-8")
    assert "stage=batch_download status=success" in log


def test_cli_batch_download_partial_failure(tmp_path, monkeypatch, capsys):
    from downloader import BatchDownloadResult

    monkeypatch.setattr(
        cli_main,
        "download_multiple_from_urls",
        lambda urls, output_dir, max_workers, on_progress=None, cancel_event=None: [
            BatchDownloadResult(index=0, url=urls[0], path=tmp_path / "0.mp4"),
            BatchDownloadResult(index=1, url=urls[1], error="network down"),
        ],
    )

    exit_code = cli_main.main(
        ["--download-urls", "https://example.com/a", "https://example.com/b",
         "--output-dir", str(tmp_path)]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Failed:" in captured.err
    assert (tmp_path / "processing.log").exists()
