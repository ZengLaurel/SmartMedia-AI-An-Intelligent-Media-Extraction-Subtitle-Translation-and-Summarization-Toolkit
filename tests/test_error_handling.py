"""Tests for roadmap Phase 2, Step 9 (error handling across all FR-39
categories, plus processing log writing per FR-40)."""

from unittest.mock import MagicMock, patch

import pytest

from ai_engine import TranscriptionError, transcribe_audio
from downloader import (
    DownloadError,
    DownloadTimeoutError,
    InputValidationError,
    download_from_url,
    import_local_file,
)
from media_processor import AudioExtractionError, extract_audio
from subtitle_generator import TranslationError, translate_segments
import importlib

from utils import ProcessingLog
import config


def test_invalid_url_category():
    with pytest.raises(InputValidationError):
        download_from_url("not-a-url")


def test_unsupported_media_format_category(tmp_path):
    bad_file = tmp_path / "notes.txt"
    bad_file.write_text("not media")
    with pytest.raises(InputValidationError):
        import_local_file(str(bad_file))


def test_download_failure_category(tmp_path):
    mock_yt_dlp = MagicMock()
    mock_yt_dlp.YoutubeDL.side_effect = RuntimeError("HTTP Error 404")

    with patch.dict("sys.modules", {"yt_dlp": mock_yt_dlp}):
        with pytest.raises(DownloadError):
            download_from_url("https://example.com/missing", output_dir=str(tmp_path))


def test_network_interruption_timeout_category(tmp_path):
    mock_yt_dlp = MagicMock()
    mock_yt_dlp.YoutubeDL.side_effect = TimeoutError("connection timed out")

    with patch.dict("sys.modules", {"yt_dlp": mock_yt_dlp}):
        with pytest.raises(DownloadTimeoutError):
            download_from_url("https://example.com/slow", output_dir=str(tmp_path))


def test_ffmpeg_execution_error_category(tmp_path):
    input_file = tmp_path / "input.mp4"
    input_file.write_bytes(b"fake video")

    failure_result = MagicMock()
    failure_result.returncode = 1
    failure_result.stderr = "Invalid data found when processing input"

    with patch("media_processor.subprocess.run", return_value=failure_result):
        with pytest.raises(AudioExtractionError):
            extract_audio(str(input_file))


def test_missing_dependency_category_ffmpeg(tmp_path):
    input_file = tmp_path / "input.mp4"
    input_file.write_bytes(b"fake video")

    with patch("media_processor.subprocess.run", side_effect=FileNotFoundError()):
        with pytest.raises(AudioExtractionError):
            extract_audio(str(input_file))


def test_missing_dependency_category_whisper(tmp_path):
    audio_file = tmp_path / "audio.wav"
    audio_file.write_bytes(b"fake wav")

    with patch("ai_engine._load_model", side_effect=TranscriptionError("not installed")):
        with pytest.raises(TranscriptionError):
            transcribe_audio(str(audio_file))


def test_missing_dependency_category_argostranslate():
    mock_argostranslate = MagicMock()
    mock_argostranslate.translate.get_installed_languages.return_value = []

    with patch.dict(
        "sys.modules",
        {
            "argostranslate": None,
            "argostranslate.package": None,
            "argostranslate.translate": None,
        },
    ):
        with pytest.raises(TranslationError):
            translate_segments([{"start": 0.0, "end": 1.0, "text": "Hi"}], "en", "zh")


def test_invalid_api_key_category(monkeypatch):
    monkeypatch.delenv("ASR_API_KEY", raising=False)
    monkeypatch.delenv("SMARTMEDIA_API_KEY", raising=False)
    importlib.reload(config)
    try:
        with pytest.raises(ValueError):
            config.require_api_key("asr")
    finally:
        importlib.reload(config)


def test_empty_low_quality_audio_category(tmp_path):
    audio_file = tmp_path / "silence.wav"
    audio_file.write_bytes(b"fake silent wav")

    model = MagicMock()
    model.transcribe.return_value = {"language": "en", "segments": []}

    with patch("ai_engine._load_model", return_value=model):
        with pytest.raises(TranscriptionError):
            transcribe_audio(str(audio_file))


def test_processing_log_written(tmp_path):
    log = ProcessingLog(str(tmp_path))
    log.record("download", "success")
    log.record("extraction", "success")
    log.record("transcription", "failed", detail="empty audio")

    log_path = log.write()

    assert log_path.exists()
    content = log_path.read_text(encoding="utf-8")
    assert "stage=download status=success" in content
    assert "stage=extraction status=success" in content
    assert "stage=transcription status=failed detail=empty audio" in content


def test_processing_log_written_on_every_run_including_empty(tmp_path):
    log = ProcessingLog(str(tmp_path))
    log_path = log.write()
    assert log_path.exists()
