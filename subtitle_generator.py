"""Bilingual subtitle generation (.srt / .vtt)."""

from pathlib import Path


class TranslationError(RuntimeError):
    """Raised when the translation engine is unavailable or fails."""


def segment_transcript(transcript: dict) -> list[dict]:
    """Return the transcript's segments, each carrying start/end/text.

    The ASR output from ai_engine.transcribe_audio is already segmented by
    timestamp; this normalizes/validates that shape for downstream use (FR-16).
    """
    segments = transcript.get("segments", [])
    return [
        {"start": seg["start"], "end": seg["end"], "text": seg["text"]}
        for seg in segments
    ]


def _load_translator(source_lang: str, target_lang: str):
    try:
        import argostranslate.package
        import argostranslate.translate
    except ImportError as exc:
        raise TranslationError(
            "argostranslate is not installed. Run `pip install argostranslate`."
        ) from exc

    installed_languages = argostranslate.translate.get_installed_languages()
    from_lang = next((l for l in installed_languages if l.code == source_lang), None)
    to_lang = next((l for l in installed_languages if l.code == target_lang), None)

    if from_lang is None or to_lang is None:
        raise TranslationError(
            f"No installed argostranslate language pair for {source_lang} -> {target_lang}. "
            "Install the matching language package first."
        )

    return from_lang.get_translation(to_lang)


def translate_segments(
    segments: list[dict],
    source_lang: str,
    target_lang: str,
) -> list[dict]:
    """Translate each segment's text from source_lang to target_lang (FR-17).

    Returns new segment dicts with an added "translated_text" key.
    Raises TranslationError if the engine is missing or a segment fails to translate.
    """
    translation = _load_translator(source_lang, target_lang)

    translated = []
    for seg in segments:
        try:
            translated_text = translation.translate(seg["text"])
        except Exception as exc:
            raise TranslationError(f"Translation failed for segment: {exc}") from exc

        translated.append({**seg, "translated_text": translated_text})

    return translated


def _format_timestamp(seconds: float, ms_separator: str) -> str:
    total_ms = round(seconds * 1000)
    hours, rem_ms = divmod(total_ms, 3_600_000)
    minutes, rem_ms = divmod(rem_ms, 60_000)
    secs, ms = divmod(rem_ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{ms_separator}{ms:03d}"


def _format_srt_timestamp(seconds: float) -> str:
    return _format_timestamp(seconds, ",")


def _format_vtt_timestamp(seconds: float) -> str:
    return _format_timestamp(seconds, ".")


def generate_srt(translated_segments: list[dict], output_path: str) -> Path:
    """Write a bilingual .srt file: each entry has the original line followed
    by the translated line (FR-18).
    """
    lines = []
    for index, seg in enumerate(translated_segments, start=1):
        start_ts = _format_srt_timestamp(seg["start"])
        end_ts = _format_srt_timestamp(seg["end"])
        lines.append(str(index))
        lines.append(f"{start_ts} --> {end_ts}")
        lines.append(seg["text"])
        lines.append(seg["translated_text"])
        lines.append("")

    path = Path(output_path)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def generate_vtt(translated_segments: list[dict], output_path: str) -> Path:
    """Write a bilingual .vtt file: each cue has the original line followed
    by the translated line (FR-19).
    """
    lines = ["WEBVTT", ""]
    for seg in translated_segments:
        start_ts = _format_vtt_timestamp(seg["start"])
        end_ts = _format_vtt_timestamp(seg["end"])
        lines.append(f"{start_ts} --> {end_ts}")
        lines.append(seg["text"])
        lines.append(seg["translated_text"])
        lines.append("")

    path = Path(output_path)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path

