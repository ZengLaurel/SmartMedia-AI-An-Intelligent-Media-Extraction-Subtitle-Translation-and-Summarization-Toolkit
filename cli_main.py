"""Command-line interface (placeholder for roadmap step 10)."""

import argparse
import sys

from downloader import InputValidationError, import_local_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="SmartMedia-AI",
        description="Intelligent audio/video processing and subtitle summarization tool",
    )
    parser.add_argument("--file", help="Path to a local media file")
    parser.add_argument("--url", help="URL of media to download")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.file and not args.url:
        parser.error("either --file or --url is required")
        return 1

    if args.file:
        try:
            import_local_file(args.file)
        except InputValidationError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        print(f"File accepted: {args.file}")
        return 0

    print("URL downloading not implemented yet (roadmap step 7).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
