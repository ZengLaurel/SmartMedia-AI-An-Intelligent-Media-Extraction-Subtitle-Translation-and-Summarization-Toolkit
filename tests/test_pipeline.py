"""Tests for the shared pipeline module (roadmap Phase 3, Step 12)."""

import threading

import pytest

import pipeline
from downloader import InputValidationError


def _options(tmp_path, **overrides):
    defaults = dict(file=str(tmp_path / "video.mp4"), url=None, source=None,
                    target="zh", format="srt", output_dir=str(tmp_path / "out"))
    defaults.update(overrides)
    return pipeline.PipelineOptions(**defaults)


def _patch_happy_path(monkeypatch, tmp_path, calls=None):
    output = tmp_path / "out"

    def record(name):
        if calls is not None:
            calls.append(name)

    def fake_extract(src, dst):
        record("extraction")
        path = output / "audio.wav"
        path.write_bytes(b"fake wav")
        return path

    monkeypatch.setattr(pipeline, "import_local_file", lambda path: record("import") or tmp_path / "video.mp4")
    monkeypatch.setattr(pipeline, "download_from_url", lambda url, output_dir: record("download") or tmp_path / "video.mp4")
    monkeypatch.setattr(pipeline, "extract_audio", fake_extract)
    monkeypatch.setattr(pipeline, "get_audio_duration", lambda path: 10.0)
    monkeypatch.setattr(pipeline, "transcribe_audio", lambda path, language=None: {
        "language": "en",
        "segments": [{"start": 0.0, "end": 1.0, "text": "Hello world."}],
    })
    monkeypatch.setattr(pipeline, "translate_segments", lambda segments, source, target: [
        {**seg, "translated_text": "你好世界。"} for seg in segments
    ])
    monkeypatch.setattr(pipeline, "generate_srt", lambda segments, path: output / "subtitles.srt")
    monkeypatch.setattr(pipeline, "generate_vtt", lambda segments, path: output / "subtitles.vtt")
    monkeypatch.setattr(pipeline, "save_summary_output", lambda text, path: output / "summary.txt")


def test_pipeline_rejects_both_file_and_url(tmp_path):
    with pytest.raises(ValueError):
        pipeline.run_pipeline(_options(tmp_path, url="https://example.com/x"))


def test_pipeline_rejects_bad_format(tmp_path):
    with pytest.raises(ValueError):
        pipeline.run_pipeline(_options(tmp_path, format="ass"))


def test_pipeline_success_returns_outputs_and_writes_log(tmp_path, monkeypatch):
    _patch_happy_path(monkeypatch, tmp_path)
    (tmp_path / "video.mp4").write_bytes(b"fake")

    outputs = pipeline.run_pipeline(_options(tmp_path))

    assert outputs["subtitles"] == tmp_path / "out" / "subtitles.srt"
    assert outputs["summary"] == tmp_path / "out" / "summary.txt"
    log = (tmp_path / "out" / "processing.log").read_text(encoding="utf-8")
    for stage in ("import", "extraction", "transcription", "subtitle_generation", "summarization"):
        assert f"stage={stage} status=success" in log
    assert "stage=pipeline status=failed" not in log


def test_pipeline_url_path_and_progress_callbacks(tmp_path, monkeypatch):
    calls = []
    _patch_happy_path(monkeypatch, tmp_path, calls)
    (tmp_path / "video.mp4").write_bytes(b"fake")

    stages = []
    pipeline.run_pipeline(_options(tmp_path, file=None, url="https://example.com/x"),
                          on_progress=stages.append)

    assert stages[0] == "download"
    assert stages == ["download", "extraction", "transcription", "subtitle generation", "summarization"]
    log = (tmp_path / "out" / "processing.log").read_text(encoding="utf-8")
    assert "stage=download status=success" in log


def test_pipeline_vtt_format(tmp_path, monkeypatch):
    _patch_happy_path(monkeypatch, tmp_path)
    (tmp_path / "video.mp4").write_bytes(b"fake")

    outputs = pipeline.run_pipeline(_options(tmp_path, format="vtt"))
    assert outputs["subtitles"] == tmp_path / "out" / "subtitles.vtt"


def test_pipeline_failure_preserves_artifacts_and_logs(tmp_path, monkeypatch):
    _patch_happy_path(monkeypatch, tmp_path)
    (tmp_path / "video.mp4").write_bytes(b"fake")

    def fail(path, language=None):
        raise InputValidationError("boom")

    monkeypatch.setattr(pipeline, "transcribe_audio", fail)

    with pytest.raises(InputValidationError):
        pipeline.run_pipeline(_options(tmp_path))

    assert (tmp_path / "out" / "audio.wav").read_bytes() == b"fake wav"
    log = (tmp_path / "out" / "processing.log").read_text(encoding="utf-8")
    assert "stage=extraction status=success" in log
    assert "stage=transcription status=failed detail=boom" in log
    assert "stage=pipeline status=failed" in log


def test_pipeline_cancel_before_start(tmp_path, monkeypatch):
    _patch_happy_path(monkeypatch, tmp_path)
    cancel = threading.Event()
    cancel.set()

    with pytest.raises(pipeline.PipelineCancelled):
        pipeline.run_pipeline(_options(tmp_path), cancel_event=cancel)

    log = (tmp_path / "out" / "processing.log").read_text(encoding="utf-8")
    assert "stage=input status=cancelled" in log
    assert "stage=pipeline status=cancelled" in log


def test_pipeline_cancel_prevents_downstream_after_translation(tmp_path, monkeypatch):
    _patch_happy_path(monkeypatch, tmp_path)
    (tmp_path / "video.mp4").write_bytes(b"fake")
    cancel = threading.Event()

    def translate_then_cancel(segments, source, target):
        cancel.set()
        return [{**seg, "translated_text": "你好世界。"} for seg in segments]

    monkeypatch.setattr(pipeline, "translate_segments", translate_then_cancel)
    generate_srt_calls = []
    monkeypatch.setattr(pipeline, "generate_srt",
                        lambda segments, path: generate_srt_calls.append(path))

    with pytest.raises(pipeline.PipelineCancelled):
        pipeline.run_pipeline(_options(tmp_path), cancel_event=cancel)

    assert generate_srt_calls == []
    log = (tmp_path / "out" / "processing.log").read_text(encoding="utf-8")
    assert "stage=subtitle generation status=cancelled" in log


def test_pipeline_cancel_prevents_next_stage_mid_run(tmp_path, monkeypatch):
    _patch_happy_path(monkeypatch, tmp_path)
    (tmp_path / "video.mp4").write_bytes(b"fake")
    cancel = threading.Event()

    def extract_then_cancel(src, dst):
        cancel.set()
        return tmp_path / "out" / "audio.wav"

    monkeypatch.setattr(pipeline, "extract_audio", extract_then_cancel)
    transcribe_calls = []
    monkeypatch.setattr(pipeline, "transcribe_audio",
                        lambda path, language=None: transcribe_calls.append(path))

    with pytest.raises(pipeline.PipelineCancelled):
        pipeline.run_pipeline(_options(tmp_path), cancel_event=cancel)

    assert transcribe_calls == []
    log = (tmp_path / "out" / "processing.log").read_text(encoding="utf-8")
    assert "stage=extraction status=cancelled" in log
