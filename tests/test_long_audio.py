"""Tests for roadmap Phase 1, Step 8 (long audio split + timeline merge)."""

from unittest.mock import MagicMock, patch

import pytest

from ai_engine import transcribe_long_audio
from media_processor import AudioExtractionError, get_audio_duration, split_audio


def _mock_ffprobe_result(duration_str: str):
    result = MagicMock()
    result.returncode = 0
    result.stdout = duration_str
    result.stderr = ""
    return result


def _mock_ffmpeg_success():
    result = MagicMock()
    result.returncode = 0
    result.stderr = ""
    return result


def test_get_audio_duration(tmp_path):
    audio_file = tmp_path / "audio.wav"
    audio_file.write_bytes(b"fake wav")

    with patch("media_processor.subprocess.run", return_value=_mock_ffprobe_result("125.4\n")):
        duration = get_audio_duration(str(audio_file))

    assert duration == 125.4


def test_split_audio_short_file_returns_original(tmp_path):
    audio_file = tmp_path / "audio.wav"
    audio_file.write_bytes(b"fake wav")

    with patch("media_processor.subprocess.run", return_value=_mock_ffprobe_result("100.0\n")):
        result = split_audio(str(audio_file), segment_seconds=1800, output_dir=str(tmp_path))

    assert result == [audio_file]


def test_audio_split_and_timeline_merge(tmp_path):
    audio_file = tmp_path / "long_audio.wav"
    audio_file.write_bytes(b"fake wav")

    def run_side_effect(command, **kwargs):
        if command[0] == "ffprobe":
            return _mock_ffprobe_result("3600.0\n")  # 1 hour -> 2 segments of 1800s
        return _mock_ffmpeg_success()

    with patch("media_processor.subprocess.run", side_effect=run_side_effect):
        chunk_paths = split_audio(str(audio_file), segment_seconds=1800, output_dir=str(tmp_path))

    assert len(chunk_paths) == 2
    assert chunk_paths[0].name == "long_audio_part000.wav"
    assert chunk_paths[1].name == "long_audio_part001.wav"


def test_transcribe_long_audio_merges_timeline(tmp_path):
    audio_file = tmp_path / "long_audio.wav"
    audio_file.write_bytes(b"fake wav")

    chunk0 = tmp_path / "long_audio_part000.wav"
    chunk1 = tmp_path / "long_audio_part001.wav"

    chunk_results = {
        str(chunk0): {
            "language": "en",
            "segments": [
                {"start": 0.0, "end": 5.0, "text": "First chunk start."},
                {"start": 5.0, "end": 10.0, "text": "First chunk end."},
            ],
        },
        str(chunk1): {
            "language": "en",
            "segments": [
                {"start": 0.0, "end": 4.0, "text": "Second chunk start."},
            ],
        },
    }

    def fake_transcribe_audio(path, language=None, model_size="base"):
        return chunk_results[path]

    with patch("ai_engine.split_audio", return_value=[chunk0, chunk1]), \
         patch("ai_engine.transcribe_audio", side_effect=fake_transcribe_audio):
        result = transcribe_long_audio(
            str(audio_file), segment_seconds=1800, temp_dir=str(tmp_path)
        )

    assert result["language"] == "en"
    assert len(result["segments"]) == 3
    # second chunk's timestamps are offset by segment_seconds (1800)
    assert result["segments"][0] == {"start": 0.0, "end": 5.0, "text": "First chunk start."}
    assert result["segments"][1] == {"start": 5.0, "end": 10.0, "text": "First chunk end."}
    assert result["segments"][2] == {"start": 1800.0, "end": 1804.0, "text": "Second chunk start."}

    # timeline must be strictly non-decreasing across the merged segments
    for prev, curr in zip(result["segments"], result["segments"][1:]):
        assert curr["start"] >= prev["start"]
