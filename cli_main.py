"""Command-line interface (placeholder for roadmap step 10)."""

import argparse
import sys


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

    print("Pipeline not implemented yet (roadmap step 1 onwards).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
