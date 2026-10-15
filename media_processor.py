"""Audio extraction and format conversion via FFmpeg."""

import math
import subprocess
from pathlib import Path

ASR_SAMPLE_RATE = 16000
ASR_CHANNELS = 1


class AudioExtractionError(RuntimeError):
    """Raised when FFmpeg fails to extract/convert audio."""


def extract_audio(input_path: str, output_path: str | None = None) -> Path:
    """Extract audio from input_path and convert it to a 16kHz mono WAV
    suitable for ASR, using FFmpeg via subprocess (IFR-04).

    Raises AudioExtractionError if FFmpeg is missing or exits non-zero.
    """
    src = Path(input_path)
    if output_path is None:
        dst = src.with_suffix(".wav")
    else:
        dst = Path(output_path)

    command = [
        "ffmpeg",
        "-y",
        "-i", str(src),
        "-vn",
        "-ac", str(ASR_CHANNELS),
        "-ar", str(ASR_SAMPLE_RATE),
        "-acodec", "pcm_s16le",
        str(dst),
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise AudioExtractionError(
            "ffmpeg executable not found. Install FFmpeg and ensure it is on PATH."
        ) from exc

    if result.returncode != 0:
        raise AudioExtractionError(
            f"ffmpeg failed (exit code {result.returncode}): {result.stderr.strip()}"
        )

    return dst


def get_audio_duration(audio_path: str) -> float:
    """Return the duration of audio_path in seconds, via ffprobe (IFR-04)."""
    command = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio_path),
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise AudioExtractionError(
            "ffprobe executable not found. Install FFmpeg and ensure it is on PATH."
        ) from exc

    if result.returncode != 0:
        raise AudioExtractionError(
            f"ffprobe failed (exit code {result.returncode}): {result.stderr.strip()}"
        )

    return float(result.stdout.strip())


def split_audio(audio_path: str, segment_seconds: int, output_dir: str) -> list[Path]:
    """Split audio_path into consecutive segments of at most segment_seconds
    each, writing them to output_dir, and return their paths in order (FR-10).

    If the audio is shorter than segment_seconds, returns a single-element
    list containing the original path unchanged.
    """
    duration = get_audio_duration(audio_path)
    if duration <= segment_seconds:
        return [Path(audio_path)]

    src = Path(audio_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    num_segments = math.ceil(duration / segment_seconds)
    segment_paths = []

    for index in range(num_segments):
        start = index * segment_seconds
        segment_path = out_dir / f"{src.stem}_part{index:03d}{src.suffix}"
        command = [
            "ffmpeg",
            "-y",
            "-i", str(src),
            "-ss", str(start),
            "-t", str(segment_seconds),
            "-c", "copy",
            str(segment_path),
        ]

        try:
            result = subprocess.run(command, capture_output=True, text=True)
        except FileNotFoundError as exc:
            raise AudioExtractionError(
                "ffmpeg executable not found. Install FFmpeg and ensure it is on PATH."
            ) from exc

        if result.returncode != 0:
            raise AudioExtractionError(
                f"ffmpeg failed splitting segment {index} (exit code {result.returncode}): "
                f"{result.stderr.strip()}"
            )

        segment_paths.append(segment_path)

    return segment_paths
