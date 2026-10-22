"""Command-line interface for the shared processing pipeline (NFR-03)."""

import sys

import config
import pipeline
from ai_engine import TranscriptionError
from downloader import DownloadError, InputValidationError
from media_processor import AudioExtractionError
from subtitle_generator import TranslationError

SUBTITLE_FORMATS = pipeline.SUBTITLE_FORMATS


def build_parser():
    import argparse

    parser = argparse.ArgumentParser(
        prog="SmartMedia-AI",
        description="Intelligent audio/video processing and subtitle summarization tool",
    )
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--file", help="Path to a local media file")
    source_group.add_argument("--url", help="URL of media to download")

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


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

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
