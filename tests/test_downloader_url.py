"""Tests for downloader.py — roadmap Phase 1, Step 7 (URL download via yt-dlp)."""

from unittest.mock import MagicMock, patch

import pytest

from downloader import (
    BatchDownloadResult,
    DownloadError,
    InputValidationError,
    download_from_url,
    download_multiple_from_urls,
    validate_url,
)


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


def test_download_multiple_rejects_empty_urls():
    with pytest.raises(InputValidationError):
        download_multiple_from_urls([], output_dir=".")


def test_download_multiple_rejects_invalid_max_workers():
    with pytest.raises(ValueError):
        download_multiple_from_urls(["https://example.com/x"], output_dir=".", max_workers=0)


def test_download_multiple_validates_each_url():
    with pytest.raises(InputValidationError):
        download_multiple_from_urls(["https://example.com/x", "not a url"], output_dir=".")


def test_download_multiple_preserves_input_order(tmp_path):
    urls = [
        "https://example.com/1",
        "https://example.com/2",
        "https://example.com/3",
    ]

    def fake_download(url, output_dir, progress_hook=None, filename_prefix=None):
        return tmp_path / f"{url.rsplit('/', 1)[-1]}.mp4"

    with patch("downloader.download_from_url", side_effect=fake_download):
        results = download_multiple_from_urls(urls, output_dir=str(tmp_path), max_workers=2)

    assert [r.index for r in results] == [0, 1, 2]
    assert [r.url for r in results] == urls
    assert all(r.path is not None and r.error is None for r in results)


def test_download_multiple_unique_filename_prefixes(tmp_path):
    prefixes = []

    def fake_download(url, output_dir, progress_hook=None, filename_prefix=None):
        prefixes.append(filename_prefix)
        return tmp_path / f"{filename_prefix}.mp4"

    with patch("downloader.download_from_url", side_effect=fake_download):
        download_multiple_from_urls(
            ["https://example.com/1", "https://example.com/2"],
            output_dir=str(tmp_path), max_workers=2,
        )

    assert len(prefixes) == 2
    assert len(set(prefixes)) == 2


def test_download_multiple_isolates_single_failure(tmp_path):
    def fake_download(url, output_dir, progress_hook=None, filename_prefix=None):
        if url.endswith("/2"):
            raise DownloadError("network down")
        return tmp_path / "ok.mp4"

    with patch("downloader.download_from_url", side_effect=fake_download):
        results = download_multiple_from_urls(
            ["https://example.com/1", "https://example.com/2", "https://example.com/3"],
            output_dir=str(tmp_path), max_workers=2,
        )

    assert results[0].path is not None
    assert results[1].error == "network down"
    assert results[2].path is not None


def test_download_multiple_limits_concurrency(tmp_path):
    import threading

    active = 0
    max_active = 0
    lock = threading.Lock()
    urls = [f"https://example.com/{i}" for i in range(6)]

    def fake_download(url, output_dir, progress_hook=None, filename_prefix=None):
        nonlocal active, max_active
        with lock:
            active += 1
            max_active = max(max_active, active)
        import time
        time.sleep(0.05)
        with lock:
            active -= 1
        return tmp_path / "ok.mp4"

    with patch("downloader.download_from_url", side_effect=fake_download):
        download_multiple_from_urls(urls, output_dir=str(tmp_path), max_workers=3)

    assert max_active <= 3
    assert max_active >= 2


def test_download_multiple_progress_carries_task_id(tmp_path):
    events = []

    def fake_download(url, output_dir, progress_hook=None, filename_prefix=None):
        if progress_hook is not None:
            progress_hook({"status": "downloading", "_percent_str": "50%"})
        return tmp_path / "ok.mp4"

    with patch("downloader.download_from_url", side_effect=fake_download):
        download_multiple_from_urls(
            ["https://example.com/1", "https://example.com/2"],
            output_dir=str(tmp_path), max_workers=2,
            on_progress=lambda index, url, data: events.append((index, url, data)),
        )

    assert len(events) == 2
    assert events[0][0] != events[1][0]


def test_download_multiple_cancel_prevents_unstarted(tmp_path):
    import threading

    started = []
    cancel = threading.Event()

    def fake_download(url, output_dir, progress_hook=None, filename_prefix=None):
        started.append(url)
        if url.endswith("/1"):
            cancel.set()
        return tmp_path / "ok.mp4"

    urls = [f"https://example.com/{i}" for i in range(1, 6)]
    with patch("downloader.download_from_url", side_effect=fake_download):
        results = download_multiple_from_urls(
            urls, output_dir=str(tmp_path), max_workers=1, cancel_event=cancel
        )

    assert any(r.cancelled for r in results)
    assert len(started) < len(urls)
