"""Tests for media_processor.py — roadmap Phase 1, Step 2 (FFmpeg audio extraction)."""

from unittest.mock import MagicMock, patch

import pytest

from media_processor import (
    ASR_CHANNELS,
    ASR_SAMPLE_RATE,
    AudioExtractionError,
    extract_audio,
)


def _mock_success_result():
    result = MagicMock()
    result.returncode = 0
    result.stderr = ""
    return result


def test_ffmpeg_audio_extraction(tmp_path):
    input_file = tmp_path / "input.mp4"
    input_file.write_bytes(b"fake video")

    with patch("media_processor.subprocess.run", return_value=_mock_success_result()) as run_mock:
        output = extract_audio(str(input_file))

    assert output.suffix == ".wav"
    run_mock.assert_called_once()
    command = run_mock.call_args[0][0]
    assert command[0] == "ffmpeg"
    assert str(input_file) in command


def test_audio_format_conversion(tmp_path):
    input_file = tmp_path / "input.mp4"
    input_file.write_bytes(b"fake video")
    output_file = tmp_path / "custom_output.wav"

    with patch("media_processor.subprocess.run", return_value=_mock_success_result()) as run_mock:
        output = extract_audio(str(input_file), str(output_file))

    assert output == output_file
    command = run_mock.call_args[0][0]
    assert str(output_file) in command


def test_audio_converted_to_asr_format(tmp_path):
    input_file = tmp_path / "input.mp4"
    input_file.write_bytes(b"fake video")

    with patch("media_processor.subprocess.run", return_value=_mock_success_result()) as run_mock:
        extract_audio(str(input_file))

    command = run_mock.call_args[0][0]
    assert "-ar" in command
    assert command[command.index("-ar") + 1] == str(ASR_SAMPLE_RATE)
    assert "-ac" in command
    assert command[command.index("-ac") + 1] == str(ASR_CHANNELS)


def test_extract_audio_ffmpeg_missing(tmp_path):
    input_file = tmp_path / "input.mp4"
    input_file.write_bytes(b"fake video")

    with patch("media_processor.subprocess.run", side_effect=FileNotFoundError()):
        with pytest.raises(AudioExtractionError):
            extract_audio(str(input_file))


def test_extract_audio_ffmpeg_nonzero_exit(tmp_path):
    input_file = tmp_path / "input.mp4"
    input_file.write_bytes(b"fake video")

    failure_result = MagicMock()
    failure_result.returncode = 1
    failure_result.stderr = "Invalid data found when processing input"

    with patch("media_processor.subprocess.run", return_value=failure_result):
        with pytest.raises(AudioExtractionError):
            extract_audio(str(input_file))
