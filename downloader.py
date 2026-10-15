"""Media acquisition: local file import / URL download (yt-dlp)."""

import re
from pathlib import Path

SUPPORTED_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".mp3", ".wav", ".m4a"}

_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


class InputValidationError(ValueError):
    """Raised when the supplied local file path or URL is invalid."""


class DownloadError(RuntimeError):
    """Raised when a URL download fails (network, missing dependency, etc.)."""


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


def validate_url(url: str) -> str:
    """Validate that the given string is a well-formed http(s) URL (FR-03).

    Raises InputValidationError if the URL is empty or does not use the
    http/https scheme.
    """
    if not url or not url.strip():
        raise InputValidationError("URL must not be empty.")

    if not _URL_RE.match(url.strip()):
        raise InputValidationError(
            f"Invalid URL: {url}. Only http:// and https:// URLs are supported."
        )

    return url.strip()


def _default_progress_hook(d: dict) -> None:
    if d.get("status") == "downloading":
        percent = d.get("_percent_str", "").strip()
        speed = d.get("_speed_str", "").strip()
        print(f"Downloading... {percent} ({speed})")
    elif d.get("status") == "finished":
        print("Download finished, post-processing...")


def download_from_url(
    url: str,
    output_dir: str = ".",
    progress_hook=None,
) -> Path:
    """Download the media at `url` using yt-dlp (IFR-03, FR-01).

    Displays download progress via progress_hook (defaults to printing
    percentage/speed to stdout) per FR-05. Returns the path to the
    downloaded file. Raises InputValidationError for a malformed URL and
    DownloadError if yt-dlp is missing or the download fails.
    """
    validated_url = validate_url(url)

    try:
        import yt_dlp
    except ImportError as exc:
        raise DownloadError(
            "yt-dlp is not installed. Run `pip install yt-dlp`."
        ) from exc

    hook = progress_hook or _default_progress_hook

    options = {
        "outtmpl": str(Path(output_dir) / "%(title)s.%(ext)s"),
        "progress_hooks": [hook],
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(validated_url, download=True)
            filename = ydl.prepare_filename(info)
    except Exception as exc:
        raise DownloadError(f"Failed to download {url}: {exc}") from exc

    return Path(filename)

