"""Command-line interface for the shared processing pipeline (NFR-03)."""

import sys
from pathlib import Path

import config
import pipeline
from ai_engine import TranscriptionError
from downloader import DownloadError, InputValidationError, download_multiple_from_urls
from media_processor import AudioExtractionError
from subtitle_generator import TranslationError
from utils import ProcessingLog

SUBTITLE_FORMATS = pipeline.SUBTITLE_FORMATS


def build_parser():
    import argparse

    parser = argparse.ArgumentParser(
        prog="SmartMedia-AI",
        description="Intelligent audio/video processing and subtitle summarization tool",
    )
    source_group = parser.add_mutually_exclusive_group(required=False)
    source_group.add_argument("--file", help="Path to a local media file")
    source_group.add_argument("--url", help="URL of media to download")
    source_group.add_argument(
        "--download-urls", nargs="+", metavar="URL",
        help="Download multiple media URLs concurrently, then stop",
    )

    parser.add_argument(
        "--max-concurrent-downloads", type=int, default=config.MAX_CONCURRENT_DOWNLOADS,
        help=f"Maximum parallel downloads (default: {config.MAX_CONCURRENT_DOWNLOADS})",
    )
    parser.add_argument(
        "--source", default=None, help="Source language code (e.g. en). Auto-detected if omitted."
    )
    parser.add_argument(
        "--target", default="zh", help="Target language code for translated subtitles (default: zh)"
    )
    parser.add_argument(
        "--format",
        choices=sorted(SUBTITLE_FORMATS),
        default="srt",
        help="Subtitle output format (default: srt)",
    )
    parser.add_argument(
        "--output-dir", default=config.OUTPUT_DIR, help="Directory for all generated artifacts"
    )
    return parser


def _run_batch_downloads(args) -> int:
    output_dir = Path(args.output_dir)
    log = ProcessingLog(str(output_dir))
    log.record("batch_download", "starting", detail=f"items={len(args.download_urls)}")
    try:
        results = download_multiple_from_urls(
            args.download_urls,
            output_dir=str(output_dir),
            max_workers=args.max_concurrent_downloads,
            on_progress=lambda index, url, data: _print_batch_progress(index, url, data),
        )
    except (InputValidationError, DownloadError, ValueError) as exc:
        log.record("batch_download", "failed", detail=str(exc))
        try:
            log_path = log.write()
            print(f"Log: {log_path}", file=sys.stderr)
        except OSError as log_error:
            print(f"Log write failed: {log_error}", file=sys.stderr)
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    failures = 0
    for result in results:
        if result.path is not None:
            print(f"[{result.index + 1}/{len(results)}] Downloaded: {result.path}")
            log.record("batch_download_item", "success", detail=f"url={result.url} path={result.path}")
        elif result.cancelled:
            failures += 1
            print(f"[{result.index + 1}/{len(results)}] Cancelled: {result.url}")
            log.record("batch_download_item", "cancelled", detail=result.url)
        else:
            failures += 1
            print(f"[{result.index + 1}/{len(results)}] Failed: {result.url}: {result.error}", file=sys.stderr)
            log.record("batch_download_item", "failed", detail=f"url={result.url} error={result.error}")
    log.record("batch_download", "failed" if failures else "success",
               detail=f"succeeded={len(results) - failures} failed={failures}")
    try:
        log_path = log.write()
    except OSError as exc:
        print(f"Downloads finished, but the processing log could not be saved: {exc}", file=sys.stderr)
        return 1
    print(f"Log: {log_path}")
    return 1 if failures else 0


def _print_batch_progress(index: int, url: str, data: dict) -> None:
    if data.get("status") == "downloading":
        percent = data.get("_percent_str", "").strip()
        speed = data.get("_speed_str", "").strip()
        print(f"[{index + 1}] {url}: {percent} ({speed})")
    elif data.get("status") == "finished":
        print(f"[{index + 1}] {url}: download finished, post-processing")


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.download_urls:
        if args.max_concurrent_downloads < 1:
            parser.error("--max-concurrent-downloads must be at least 1")
        if args.source is not None or args.target != "zh" or args.format != "srt":
            parser.error("--source, --target, and --format apply only to single-item processing")
        return _run_batch_downloads(args)

    if args.file is None and args.url is None:
        parser.error("either --file, --url, or --download-urls is required")

    options = pipeline.PipelineOptions(
        file=args.file,
        url=args.url,
        source=args.source,
        target=args.target,
        format=args.format,
        output_dir=args.output_dir,
    )

    def on_progress(stage: str) -> None:
        print(f"[{stage}] starting...")

    try:
        outputs = pipeline.run_pipeline(options, on_progress=on_progress)
    except (InputValidationError, DownloadError, AudioExtractionError,
            TranscriptionError, TranslationError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1

    print("\nPipeline completed successfully. Output files:")
    print(f"  Audio:     {outputs['audio']}")
    print(f"  Transcript: {outputs['transcript']}")
    print(f"  Subtitles:  {outputs['subtitles']}")
    print(f"  Summary:    {outputs['summary']}")
    print(f"  Log:        {outputs['log']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
