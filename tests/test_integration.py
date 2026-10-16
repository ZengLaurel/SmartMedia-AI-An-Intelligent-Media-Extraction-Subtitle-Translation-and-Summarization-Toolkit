"""End-to-end integration test for roadmap Phase 2, Step 11.

Exercises the full pipeline chain (downloader -> media_processor ->
ai_engine -> subtitle_generator -> summarizer) through cli_main.main(),
with every external dependency (FFmpeg, Whisper, argostranslate) mocked
so this runs in CI without a live network connection or real API calls
(NFR-06, NFR-09).
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import cli_main


def _mock_ffmpeg_success(command, **kwargs):
    """Mimic ffmpeg/ffprobe: ffprobe (duration query) just returns stdout;
    ffmpeg (extraction/split) must also materialize the output file it was
    asked to produce, since downstream code checks the file actually exists.
    """
    result = MagicMock()
    result.returncode = 0
    result.stderr = ""

    if command[0] == "ffprobe":
        result.stdout = "12.5\n"
    else:
        output_path = Path(command[-1])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"fake audio data")
        result.stdout = ""

    return result


def _mock_whisper_model():
    model = MagicMock()
    model.transcribe.return_value = {
        "language": "en",
        "segments": [
            {"start": 0.0, "end": 2.0, "text": "Hello from the integration test."},
            {"start": 2.0, "end": 4.5, "text": "This covers the full pipeline."},
        ],
    }
    return model


def _mock_translation():
    translation_table = {
        "Hello from the integration test.": "来自集成测试的问候。",
        "This covers the full pipeline.": "这覆盖了完整的流水线。",
    }

    mock_translation = MagicMock()
    mock_translation.translate.side_effect = lambda text: translation_table[text]

    mock_lang_en = MagicMock()
    mock_lang_en.code = "en"
    mock_lang_en.get_translation.return_value = mock_translation

    mock_lang_zh = MagicMock()
    mock_lang_zh.code = "zh"

    mock_argostranslate = MagicMock()
    mock_argostranslate.translate.get_installed_languages.return_value = [
        mock_lang_en,
        mock_lang_zh,
    ]
    return mock_argostranslate


def test_full_pipeline_integration_local_file(tmp_path, capsys):
    video_file = tmp_path / "sample.mp4"
    video_file.write_bytes(b"fake video content")

    output_dir = tmp_path / "output"

    mock_argostranslate = _mock_translation()
    mock_whisper = MagicMock()
    mock_whisper.load_model.return_value = _mock_whisper_model()

    with patch("media_processor.subprocess.run", side_effect=_mock_ffmpeg_success), \
         patch.dict(
             "sys.modules",
             {
                 "whisper": mock_whisper,
                 "argostranslate": mock_argostranslate,
                 "argostranslate.package": MagicMock(),
                 "argostranslate.translate": mock_argostranslate.translate,
             },
         ):
        exit_code = cli_main.main(
            [
                "--file", str(video_file),
                "--source", "en",
                "--target", "zh",
                "--format", "srt",
                "--output-dir", str(output_dir),
            ]
        )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Pipeline completed successfully" in captured.out

    # every stage's artifact must exist on disk
    assert (output_dir / "audio.wav").exists()
    assert (output_dir / "transcript.txt").exists()
    assert (output_dir / "subtitles.srt").exists()
    assert (output_dir / "summary.txt").exists()
    assert (output_dir / "processing.log").exists()

    # bilingual subtitle content must contain both source and translated text
    srt_content = (output_dir / "subtitles.srt").read_text(encoding="utf-8")
    assert "Hello from the integration test." in srt_content
    assert "来自集成测试的问候。" in srt_content

    # the processing log must record every stage that ran
    log_content = (output_dir / "processing.log").read_text(encoding="utf-8")
    for stage in ["import", "extraction", "transcription", "subtitle_generation", "summarization"]:
        assert f"stage={stage}" in log_content
        assert "status=success" in log_content


def test_full_pipeline_integration_vtt_format(tmp_path):
    video_file = tmp_path / "sample.mp4"
    video_file.write_bytes(b"fake video content")

    output_dir = tmp_path / "output"

    mock_argostranslate = _mock_translation()
    mock_whisper = MagicMock()
    mock_whisper.load_model.return_value = _mock_whisper_model()

    with patch("media_processor.subprocess.run", side_effect=_mock_ffmpeg_success), \
         patch.dict(
             "sys.modules",
             {
                 "whisper": mock_whisper,
                 "argostranslate": mock_argostranslate,
                 "argostranslate.package": MagicMock(),
                 "argostranslate.translate": mock_argostranslate.translate,
             },
         ):
        exit_code = cli_main.main(
            [
                "--file", str(video_file),
                "--target", "zh",
                "--format", "vtt",
                "--output-dir", str(output_dir),
            ]
        )

    assert exit_code == 0
    assert (output_dir / "subtitles.vtt").exists()
    vtt_content = (output_dir / "subtitles.vtt").read_text(encoding="utf-8")
    assert vtt_content.startswith("WEBVTT")


def test_full_pipeline_integration_failure_does_not_lose_prior_artifacts(tmp_path):
    """A later-stage failure (NFR-05) must not delete artifacts already
    produced by earlier stages (e.g. the extracted audio)."""
    video_file = tmp_path / "sample.mp4"
    video_file.write_bytes(b"fake video content")

    output_dir = tmp_path / "output"

    mock_whisper = MagicMock()
    mock_whisper.load_model.return_value = MagicMock(
        transcribe=MagicMock(return_value={"language": "en", "segments": []})
    )

    with patch("media_processor.subprocess.run", side_effect=_mock_ffmpeg_success), \
         patch.dict("sys.modules", {"whisper": mock_whisper}):
        exit_code = cli_main.main(
            ["--file", str(video_file), "--output-dir", str(output_dir)]
        )

    assert exit_code == 1
    # extraction succeeded before transcription failed; its artifact must remain
    assert (output_dir / "audio.wav").exists()
    assert (output_dir / "processing.log").exists()
    log_content = (output_dir / "processing.log").read_text(encoding="utf-8")
    assert "stage=extraction status=success" in log_content
    assert "stage=pipeline status=failed" in log_content
