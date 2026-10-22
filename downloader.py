"""Media acquisition: local file import / URL download (yt-dlp)."""

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from threading import Event
from typing import Callable

SUPPORTED_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".mp3", ".wav", ".m4a"}

_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


class InputValidationError(ValueError):
    """Raised when the supplied local file path or URL is invalid."""


class DownloadError(RuntimeError):
    """Raised when a URL download fails (network, missing dependency, etc.)."""


class DownloadTimeoutError(DownloadError):
    """Raised when a URL download exceeds the configured socket timeout
    (FR-39: API timeout / network interruption).
    """


DEFAULT_SOCKET_TIMEOUT_SECONDS = 30
DEFAULT_MAX_CONCURRENT_DOWNLOADS = 3


@dataclass(frozen=True)
class BatchDownloadResult:
    index: int
    url: str
    path: Path | None = None
    error: str | None = None
    cancelled: bool = False


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
    socket_timeout: int = DEFAULT_SOCKET_TIMEOUT_SECONDS,
    filename_prefix: str | None = None,
) -> Path:
    """Download the media at `url` using yt-dlp (IFR-03, FR-01).

    Displays download progress via progress_hook (defaults to printing
    percentage/speed to stdout) per FR-05. Returns the path to the
    downloaded file. Raises InputValidationError for a malformed URL,
    DownloadTimeoutError if the connection exceeds socket_timeout (FR-39),
    and DownloadError if yt-dlp is missing or the download otherwise fails.
    """
    validated_url = validate_url(url)

    try:
        import yt_dlp
    except ImportError as exc:
        raise DownloadError(
            "yt-dlp is not installed. Run `pip install yt-dlp`."
        ) from exc

    hook = progress_hook or _default_progress_hook
    template = "%(title)s.%(ext)s"
    if filename_prefix is not None:
        template = f"{filename_prefix}_%(title)s.%(ext)s"

    options = {
        "outtmpl": str(Path(output_dir) / template),
        "progress_hooks": [hook],
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": socket_timeout,
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(validated_url, download=True)
            filename = ydl.prepare_filename(info)
    except Exception as exc:
        if "timed out" in str(exc).lower() or isinstance(exc, TimeoutError):
            raise DownloadTimeoutError(
                f"Download timed out after {socket_timeout}s for {url}: {exc}"
            ) from exc
        raise DownloadError(f"Failed to download {url}: {exc}") from exc

    return Path(filename)


def download_multiple_from_urls(
    urls: list[str],
    output_dir: str,
    max_workers: int = DEFAULT_MAX_CONCURRENT_DOWNLOADS,
    on_progress: Callable[[int, str, dict], None] | None = None,
    cancel_event: Event | None = None,
) -> list[BatchDownloadResult]:
    """Download several URLs concurrently, retaining input-order results.

    Each task receives a unique filename prefix to prevent collisions when
    different URLs yield media with the same title. Cancellation prevents
    not-yet-started downloads and waits for active yt-dlp calls to finish.
    """
    if not urls:
        raise InputValidationError("At least one URL is required.")
    if max_workers < 1:
        raise ValueError("max_workers must be at least 1.")

    validated_urls = [validate_url(url) for url in urls]
    results: list[BatchDownloadResult | None] = [None] * len(validated_urls)

    def download_one(index: int, url: str) -> BatchDownloadResult:
        if cancel_event is not None and cancel_event.is_set():
            return BatchDownloadResult(index=index, url=url, cancelled=True)

        last_sent = [0.0]

        def hook(data: dict) -> None:
            if on_progress is not None:
                import time

                now = time.monotonic()
                if data.get("status") != "downloading" or now - last_sent[0] >= 0.2:
                    last_sent[0] = now
                    on_progress(index, url, dict(data))

        try:
            path = download_from_url(
                url,
                output_dir=output_dir,
                progress_hook=hook,
                filename_prefix=f"{index + 1:03d}",
            )
        except Exception as exc:
            return BatchDownloadResult(index=index, url=url, error=str(exc))
        return BatchDownloadResult(index=index, url=url, path=path)

    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="media-download") as executor:
        futures = {
            executor.submit(download_one, index, url): (index, url)
            for index, url in enumerate(validated_urls)
        }
        for future in as_completed(futures):
            index, url = futures[future]
            try:
                results[index] = future.result()
            except Exception as exc:
                results[index] = BatchDownloadResult(index=index, url=url, error=str(exc))

    if cancel_event is not None and cancel_event.is_set():
        results = [
            result if result is not None else BatchDownloadResult(
                index=index, url=url, cancelled=True
            )
            for index, (url, result) in enumerate(zip(validated_urls, results))
        ]

    return [result for result in results if result is not None]

