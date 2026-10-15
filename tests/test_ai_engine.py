"""Tests for ai_engine.py — roadmap Phase 1, Step 3 (ASR transcription)."""

from unittest.mock import MagicMock, patch

import pytest

from ai_engine import TranscriptionError, transcribe_audio


def _mock_model(result):
    model = MagicMock()
    model.transcribe.return_value = result
    return model


def test_asr_transcription(tmp_path):
    audio_file = tmp_path / "audio.wav"
    audio_file.write_bytes(b"fake wav")

    whisper_result = {
        "language": "en",
        "segments": [
            {"start": 0.0, "end": 2.5, "text": " Hello world."},
        ],
    }

    with patch("ai_engine._load_model", return_value=_mock_model(whisper_result)):
        result = transcribe_audio(str(audio_file))

    assert result["language"] == "en"
    assert len(result["segments"]) == 1
    assert result["segments"][0]["text"] == "Hello world."


def test_transcript_has_timestamps(tmp_path):
    audio_file = tmp_path / "audio.wav"
    audio_file.write_bytes(b"fake wav")

    whisper_result = {
        "language": "en",
        "segments": [
            {"start": 0.0, "end": 1.2, "text": "First."},
            {"start": 1.2, "end": 3.0, "text": "Second."},
        ],
    }

    with patch("ai_engine._load_model", return_value=_mock_model(whisper_result)):
        result = transcribe_audio(str(audio_file))

    for seg in result["segments"]:
        assert "start" in seg and "end" in seg
        assert seg["end"] > seg["start"]


def test_transcription_en_zh(tmp_path):
    audio_file = tmp_path / "audio.wav"
    audio_file.write_bytes(b"fake wav")

    en_result = {"language": "en", "segments": [{"start": 0.0, "end": 1.0, "text": "Hello."}]}
    zh_result = {"language": "zh", "segments": [{"start": 0.0, "end": 1.0, "text": "你好。"}]}

    with patch("ai_engine._load_model", return_value=_mock_model(en_result)):
        result_en = transcribe_audio(str(audio_file), language="en")
    with patch("ai_engine._load_model", return_value=_mock_model(zh_result)):
        result_zh = transcribe_audio(str(audio_file), language="zh")

    assert result_en["language"] == "en"
    assert result_zh["language"] == "zh"


def test_auto_language_detection(tmp_path):
    audio_file = tmp_path / "audio.wav"
    audio_file.write_bytes(b"fake wav")

    whisper_result = {"language": "zh", "segments": [{"start": 0.0, "end": 1.0, "text": "你好。"}]}
    mock_model = _mock_model(whisper_result)

    with patch("ai_engine._load_model", return_value=mock_model):
        result = transcribe_audio(str(audio_file), language=None)

    mock_model.transcribe.assert_called_once()
    _, kwargs = mock_model.transcribe.call_args
    assert kwargs["language"] is None
    assert result["language"] == "zh"


def test_transcription_failure_halts_pipeline_empty_result(tmp_path):
    audio_file = tmp_path / "silence.wav"
    audio_file.write_bytes(b"fake silent wav")

    empty_result = {"language": "en", "segments": []}

    with patch("ai_engine._load_model", return_value=_mock_model(empty_result)):
        with pytest.raises(TranscriptionError):
            transcribe_audio(str(audio_file))


def test_transcription_failure_halts_pipeline_exception(tmp_path):
    audio_file = tmp_path / "corrupted.wav"
    audio_file.write_bytes(b"not real audio")

    model = MagicMock()
    model.transcribe.side_effect = RuntimeError("decode error")

    with patch("ai_engine._load_model", return_value=model):
        with pytest.raises(TranscriptionError):
            transcribe_audio(str(audio_file))


def test_transcription_missing_file():
    with pytest.raises(TranscriptionError):
        transcribe_audio("does_not_exist.wav")
