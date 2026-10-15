"""Tests for downloader.py — roadmap Phase 1, Step 7 (URL download via yt-dlp)."""

from unittest.mock import MagicMock, patch

import pytest

from downloader import DownloadError, InputValidationError, download_from_url, validate_url


def test_validate_url_accepts_http_and_https():
    assert validate_url("https://example.com/video") == "https://example.com/video"
    assert validate_url("http://example.com/video") == "http://example.com/video"


def test_validate_url_rejects_empty():
    with pytest.raises(InputValidationError):
        validate_url("")


def test_validate_url_rejects_non_url():
    with pytest.raises(InputValidationError):
        validate_url("not a url")
    with pytest.raises(InputValidationError):
        validate_url("ftp://example.com/file")


def _mock_yt_dlp_module(info: dict, filename: str):
    mock_ydl_instance = MagicMock()
    mock_ydl_instance.extract_info.return_value = info
    mock_ydl_instance.prepare_filename.return_value = filename
    mock_ydl_instance.__enter__.return_value = mock_ydl_instance
    mock_ydl_instance.__exit__.return_value = False

    mock_yt_dlp = MagicMock()
    mock_yt_dlp.YoutubeDL.return_value = mock_ydl_instance
    return mock_yt_dlp, mock_ydl_instance


def test_download_via_url(tmp_path):
    mock_yt_dlp, mock_instance = _mock_yt_dlp_module(
        info={"title": "Sample Video", "ext": "mp4"},
        filename=str(tmp_path / "Sample Video.mp4"),
    )

    with patch.dict("sys.modules", {"yt_dlp": mock_yt_dlp}):
        result = download_from_url("https://example.com/watch?v=abc123", output_dir=str(tmp_path))

    assert result == tmp_path / "Sample Video.mp4"
    mock_instance.extract_info.assert_called_once()


def test_download_via_url_invalid_url_raises_before_yt_dlp():
    with pytest.raises(InputValidationError):
        download_from_url("not-a-url")


def test_download_via_url_missing_dependency(tmp_path):
    with patch.dict("sys.modules", {"yt_dlp": None}):
        with pytest.raises(DownloadError):
            download_from_url("https://example.com/watch?v=abc123", output_dir=str(tmp_path))


def test_download_via_url_failure_wrapped(tmp_path):
    mock_yt_dlp = MagicMock()
    mock_yt_dlp.YoutubeDL.side_effect = RuntimeError("network unreachable")

    with patch.dict("sys.modules", {"yt_dlp": mock_yt_dlp}):
        with pytest.raises(DownloadError):
            download_from_url("https://example.com/watch?v=abc123", output_dir=str(tmp_path))


def test_download_progress_indicator(tmp_path):
    mock_yt_dlp, mock_instance = _mock_yt_dlp_module(
        info={"title": "Sample Video", "ext": "mp4"},
        filename=str(tmp_path / "Sample Video.mp4"),
    )

    received_events = []

    def custom_hook(d):
        received_events.append(d)

    with patch.dict("sys.modules", {"yt_dlp": mock_yt_dlp}):
        download_from_url(
            "https://example.com/watch?v=abc123",
            output_dir=str(tmp_path),
            progress_hook=custom_hook,
        )

    call_kwargs = mock_yt_dlp.YoutubeDL.call_args[0][0]
    assert custom_hook in call_kwargs["progress_hooks"]
