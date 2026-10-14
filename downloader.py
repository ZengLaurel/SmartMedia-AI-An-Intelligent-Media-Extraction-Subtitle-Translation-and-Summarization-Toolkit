"""Media acquisition: local file import / URL download (yt-dlp)."""

from pathlib import Path

SUPPORTED_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".mp3", ".wav", ".m4a"}


class InputValidationError(ValueError):
    """Raised when the supplied local file path or URL is invalid."""


def import_local_file(path: str) -> Path:
    """Validate a local media file path and return it as a Path.

    Raises InputValidationError if the file does not exist or has an
    unsupported extension, per FR-02 / FR-03.
    """
    file_path = Path(path)

    if not file_path.exists():
        raise InputValidationError(f"File not found: {path}")

    if not file_path.is_file():
        raise InputValidationError(f"Not a file: {path}")

    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise InputValidationError(
            f"Unsupported file extension '{file_path.suffix}' for {path}. "
            f"Supported extensions: {supported}"
        )

    return file_path

