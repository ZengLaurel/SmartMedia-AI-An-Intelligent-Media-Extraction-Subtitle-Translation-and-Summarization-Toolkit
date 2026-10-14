"""Audio extraction and format conversion via FFmpeg."""

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
