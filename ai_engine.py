"""AI engine: speech transcription (ASR) via Whisper, translation."""

from pathlib import Path

DEFAULT_MODEL_SIZE = "base"
SUPPORTED_LANGUAGES = {"en", "zh"}


class TranscriptionError(RuntimeError):
    """Raised when ASR transcription fails or yields no usable text."""


def _load_model(model_size: str):
    try:
        import whisper
    except ImportError as exc:
        raise TranscriptionError(
            "openai-whisper is not installed. Run `pip install openai-whisper`."
        ) from exc

    return whisper.load_model(model_size)


def transcribe_audio(
    audio_path: str,
    language: str | None = None,
    model_size: str = DEFAULT_MODEL_SIZE,
) -> dict:
    """Transcribe a WAV file into timestamped segments using Whisper.

    If `language` is None, Whisper auto-detects the spoken language (FR-14).
    Returns a dict: {"language": str, "segments": [{"start", "end", "text"}, ...]}.
    Raises TranscriptionError if the audio is missing, unreadable, or the
    transcription is empty (FR-15).
    """
    path = Path(audio_path)
    if not path.exists():
        raise TranscriptionError(f"Audio file not found: {audio_path}")

    model = _load_model(model_size)

    try:
        result = model.transcribe(str(path), language=language)
    except Exception as exc:
        raise TranscriptionError(f"Whisper transcription failed: {exc}") from exc

    segments = [
        {
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"].strip(),
        }
        for seg in result.get("segments", [])
        if seg.get("text", "").strip()
    ]

    if not segments:
        raise TranscriptionError(
            f"Transcription produced no usable text for {audio_path} "
            "(audio may be silent, corrupted, or unintelligible)."
        )

    return {
        "language": result.get("language", language),
        "segments": segments,
    }

