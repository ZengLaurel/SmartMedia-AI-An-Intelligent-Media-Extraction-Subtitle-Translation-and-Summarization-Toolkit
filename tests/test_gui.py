"""Headless tests for desktop task control and shared backend parity."""

import queue
import threading
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import cli_main
import gui_app
import pipeline


def test_gui_options_map_to_backend():
    options = gui_app.build_options("file", " video.mp4 ", "unused", "自动检测",
                                    "中文 (zh)", "vtt", " output ")
    assert options == pipeline.PipelineOptions(file="video.mp4", format="vtt", output_dir="output")
    options = gui_app.build_options("url", "unused", "https://example.com/video", "中文 (zh)",
                                    "英语 (en)", "srt", "output")
    assert options.file is None
    assert options.url == "https://example.com/video"
    assert options.source == "zh"
    assert options.target == "en"


@pytest.mark.parametrize("mode,file,url,output", [
    ("file", "", "", "output"),
    ("url", "", " ", "output"),
    ("file", "video.mp4", "", " "),
])
def test_gui_rejects_missing_input(mode, file, url, output):
    with pytest.raises(ValueError):
        gui_app.build_options(mode, file, url, "自动检测", "中文 (zh)", "srt", output)


def test_worker_queues_progress_and_single_terminal_event(monkeypatch):
    caller_thread = threading.get_ident()

    def fake_run(options, on_progress, cancel_event):
        assert threading.get_ident() != caller_thread
        on_progress("extraction")
        return {"summary": Path("summary.txt")}

    monkeypatch.setattr(pipeline, "run_pipeline", fake_run)
    worker = gui_app.PipelineWorker()
    worker.start(pipeline.PipelineOptions(file="sample.mp4"))
    worker.thread.join(timeout=5)
    assert not worker.running
    assert worker.events.get_nowait() == ("progress", "extraction")
    assert worker.events.get_nowait() == ("success", {"summary": Path("summary.txt")})
    assert worker.events.empty()


def test_worker_cancel_blocks_restart_until_current_stage_returns(monkeypatch):
    entered = threading.Event()
    release = threading.Event()

    def fake_run(options, on_progress, cancel_event):
        entered.set()
        assert release.wait(timeout=5)
        if cancel_event.is_set():
            raise pipeline.PipelineCancelled()
        return {}

    monkeypatch.setattr(pipeline, "run_pipeline", fake_run)
    worker = gui_app.PipelineWorker()
    options = pipeline.PipelineOptions(file="sample.mp4")
    worker.start(options)
    try:
        assert entered.wait(timeout=5)
        worker.cancel()
        assert worker.running
        with pytest.raises(RuntimeError):
            worker.start(options)
    finally:
        release.set()
        worker.thread.join(timeout=5)
    assert not worker.running
    assert worker.events.get_nowait() == ("cancelled", None)
    assert worker.events.empty()


def test_worker_reports_failure_and_can_restart(monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("log write failed")

    monkeypatch.setattr(pipeline, "run_pipeline", fail)
    worker = gui_app.PipelineWorker()
    options = pipeline.PipelineOptions(file="sample.mp4")
    worker.start(options)
    worker.thread.join(timeout=5)
    assert worker.events.get_nowait() == ("error", "log write failed")
    monkeypatch.setattr(pipeline, "run_pipeline", lambda *args, **kwargs: {})
    worker.start(options)
    worker.thread.join(timeout=5)
    assert worker.events.get_nowait() == ("success", {})


def _fake_view(tmp_path):
    app = gui_app.SmartMediaApp.__new__(gui_app.SmartMediaApp)
    app.root = MagicMock()
    app.worker = gui_app.PipelineWorker()
    app.busy = True
    app.closing = False
    app.pending_result = None
    app.output_directory = tmp_path
    app.batch_mode = False
    app.progress = MagicMock()
    app.start_button = MagicMock()
    app.cancel_button = MagicMock()
    app.open_button = MagicMock()
    app.status = MagicMock()
    app.subtitle_preview = MagicMock()
    app.summary_preview = MagicMock()
    app._input_states = MagicMock()
    return app


def test_gui_preview_success_and_state_recovery(tmp_path):
    subtitles = tmp_path / "subtitles.srt"
    summary = tmp_path / "summary.txt"
    subtitles.write_text("Hello\n你好", encoding="utf-8")
    summary.write_text("Summary\nKeywords", encoding="utf-8")
    app = _fake_view(tmp_path)
    app._finish("success", {"subtitles": subtitles, "summary": summary})
    assert not app.busy
    app.subtitle_preview.insert.assert_called_once_with("1.0", "Hello\n你好")
    app.summary_preview.insert.assert_called_once_with("1.0", "Summary\nKeywords")
    app.start_button.configure.assert_called_with(state="normal")
    app.cancel_button.configure.assert_called_with(state="disabled")


def test_gui_preview_failure_does_not_change_success_status(tmp_path, monkeypatch):
    dialog = MagicMock()
    monkeypatch.setattr("tkinter.messagebox.showerror", dialog)
    app = _fake_view(tmp_path)
    app._finish("success", {"subtitles": tmp_path / "missing.srt", "summary": tmp_path / "summary.txt"})
    assert not app.busy
    assert "处理完成，但预览读取失败" in app.status.set.call_args.args[0]
    dialog.assert_called_once()


def test_gui_failure_restores_controls_and_surfaces_error(tmp_path, monkeypatch):
    dialog = MagicMock()
    monkeypatch.setattr("tkinter.messagebox.showerror", dialog)
    app = _fake_view(tmp_path)
    app._finish("error", "ffmpeg not found")
    assert not app.busy
    assert "ffmpeg not found" in app.status.set.call_args.args[0]
    dialog.assert_called_once()


def test_gui_close_waits_for_terminal_message(tmp_path):
    app = _fake_view(tmp_path)
    app.close()
    assert app.closing
    assert app.worker.cancel_event.is_set()
    app.root.destroy.assert_not_called()
    app.worker.events.put(("cancelled", None))
    app._poll()
    assert not app.busy
    app.root.destroy.assert_called_once()


def test_gui_open_directory_failure(tmp_path, monkeypatch):
    def fail(path):
        raise OSError("Cannot open folder")

    monkeypatch.setattr(gui_app, "open_output_directory", fail)
    dialog = MagicMock()
    monkeypatch.setattr("tkinter.messagebox.showerror", dialog)
    app = _fake_view(tmp_path)
    app.open_output()
    assert "Cannot open folder" in app.status.set.call_args.args[0]
    dialog.assert_called_once()


def test_open_directory_uses_safe_argument_list(tmp_path, monkeypatch):
    monkeypatch.setattr(gui_app.sys, "platform", "linux")
    popen = MagicMock()
    monkeypatch.setattr(gui_app.subprocess, "Popen", popen)
    gui_app.open_output_directory(tmp_path)
    popen.assert_called_once_with(["xdg-open", str(tmp_path.resolve())])
    with pytest.raises(OSError):
        gui_app.open_output_directory(tmp_path / "missing")


@pytest.mark.parametrize("subtitle_format", ["srt", "vtt"])
def test_gui_cli_backend_parity(tmp_path, monkeypatch, subtitle_format):
    video = tmp_path / "sample.mp4"
    video.write_bytes(b"video")
    stages = []

    def extract(src, dst):
        stages.append("extraction")
        path = Path(dst)
        path.write_bytes(b"audio")
        return path

    def transcribe(path, language=None):
        stages.append("transcription")
        return {"language": "en", "segments": [
            {"start": 0.0, "end": 1.5, "text": "Hello world."},
            {"start": 1.5, "end": 3.0, "text": "A shared pipeline."},
        ]}

    def translate(segments, source, target):
        stages.append("translation")
        assert source == "en" and target == "zh"
        return [{**seg, "translated_text": "测试译文"} for seg in segments]

    monkeypatch.setattr(pipeline, "extract_audio", extract)
    monkeypatch.setattr(pipeline, "get_audio_duration", lambda path: 3.0)
    monkeypatch.setattr(pipeline, "transcribe_audio", transcribe)
    monkeypatch.setattr(pipeline, "translate_segments", translate)
    cli_dir = tmp_path / "cli"
    assert cli_main.main(["--file", str(video), "--format", subtitle_format,
                          "--output-dir", str(cli_dir)]) == 0
    cli_stages = list(stages)
    stages.clear()
    gui_dir = tmp_path / "gui"
    options = gui_app.build_options("file", str(video), "", "自动检测", "中文 (zh)",
                                    subtitle_format, str(gui_dir))
    worker = gui_app.PipelineWorker()
    worker.start(options)
    worker.thread.join(timeout=5)
    assert not worker.running
    events = []
    while not worker.events.empty():
        events.append(worker.events.get_nowait())
    assert events[-1][0] == "success"
    assert stages == cli_stages
    for filename in ("audio.wav", "transcript.txt", "subtitles." + subtitle_format, "summary.txt"):
        assert (cli_dir / filename).read_bytes() == (gui_dir / filename).read_bytes()


def test_batch_download_worker_queues_progress_and_complete(monkeypatch):
    from downloader import BatchDownloadResult

    results = [
        BatchDownloadResult(index=0, url="https://example.com/a", path=Path("a.mp4")),
        BatchDownloadResult(index=1, url="https://example.com/b", error="fail"),
    ]

    def fake_download(urls, output_dir, max_workers, on_progress=None, cancel_event=None):
        on_progress(0, urls[0], {"status": "downloading", "_percent_str": "10%"})
        return results

    monkeypatch.setattr(gui_app, "download_multiple_from_urls", fake_download)
    worker = gui_app.BatchDownloadWorker()
    worker.start(["https://example.com/a", "https://example.com/b"], "out", 2)
    worker.thread.join(timeout=5)
    assert not worker.running
    events = []
    while not worker.events.empty():
        events.append(worker.events.get_nowait())
    assert events[0] == ("progress", 0, "https://example.com/a",
                         {"status": "downloading", "_percent_str": "10%"})
    assert events[-1] == ("complete", results)


def test_batch_download_worker_cancel_blocks_restart(monkeypatch):
    import threading

    entered = threading.Event()
    release = threading.Event()

    def fake_download(urls, output_dir, max_workers, on_progress=None, cancel_event=None):
        entered.set()
        assert release.wait(timeout=5)
        return []

    monkeypatch.setattr(gui_app, "download_multiple_from_urls", fake_download)
    worker = gui_app.BatchDownloadWorker()
    worker.start(["https://example.com/a"], "out", 2)
    try:
        assert entered.wait(timeout=5)
        worker.cancel()
        assert worker.running
        with pytest.raises(RuntimeError):
            worker.start(["https://example.com/b"], "out", 2)
    finally:
        release.set()
        worker.thread.join(timeout=5)
    assert not worker.running


def test_batch_download_worker_reports_error(monkeypatch):
    def fake_download(urls, output_dir, max_workers, on_progress=None, cancel_event=None):
        raise ValueError("max_workers must be at least 1")

    monkeypatch.setattr(gui_app, "download_multiple_from_urls", fake_download)
    worker = gui_app.BatchDownloadWorker()
    worker.start(["https://example.com/a"], "out", 0)
    worker.thread.join(timeout=5)
    assert not worker.running
    assert worker.events.get_nowait() == ("error", "max_workers must be at least 1")
