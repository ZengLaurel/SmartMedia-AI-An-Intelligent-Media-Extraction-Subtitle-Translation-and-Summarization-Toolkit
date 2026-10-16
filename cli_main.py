"""Command-line interface: argparse-driven entry point for the full pipeline
(IFR-01). Shares the same backend modules as any future GUI (NFR-03) --
no pipeline logic is implemented here beyond orchestration and printing.
"""

import sys
from pathlib import Path

import config
from ai_engine import TranscriptionError, transcribe_audio, transcribe_long_audio
from downloader import (
    DownloadError,
    InputValidationError,
    download_from_url,
    import_local_file,
)
from media_processor import AudioExtractionError, extract_audio, get_audio_duration
from subtitle_generator import (
    TranslationError,
    generate_srt,
    generate_vtt,
    segment_transcript,
    translate_segments,
)
from summarizer import save_summary_output
from utils import ProcessingLog

SUBTITLE_FORMATS = {"srt", "vtt"}


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


def _print_stage(stage: str) -> None:
    print(f"[{stage}] starting...")


def run_pipeline(args, log: ProcessingLog) -> dict:
    """Run the full pipeline and return a dict of output paths.

    Raises on failure; callers are responsible for catching and reporting.
    """
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.url:
        _print_stage("download")
        media_path = download_from_url(args.url, output_dir=str(output_dir))
        log.record("download", "success", detail=str(media_path))
    else:
        _print_stage("import")
        media_path = import_local_file(args.file)
        log.record("import", "success", detail=str(media_path))

    _print_stage("extraction")
    audio_path = extract_audio(str(media_path), str(output_dir / "audio.wav"))
    log.record("extraction", "success", detail=str(audio_path))

    _print_stage("transcription")
    duration = get_audio_duration(str(audio_path))
    if duration > config.MAX_AUDIO_SEGMENT_SECONDS:
        transcript = transcribe_long_audio(
            str(audio_path),
            segment_seconds=config.MAX_AUDIO_SEGMENT_SECONDS,
            temp_dir=str(output_dir / "chunks"),
            language=args.source,
        )
    else:
        transcript = transcribe_audio(str(audio_path), language=args.source)
    log.record("transcription", "success", detail=f"{len(transcript['segments'])} segments")

    transcript_path = output_dir / "transcript.txt"
    transcript_path.write_text(
        "\n".join(seg["text"] for seg in transcript["segments"]), encoding="utf-8"
    )

    _print_stage("subtitle generation")
    source_lang = args.source or transcript["language"]
    segments = segment_transcript(transcript)
    translated = translate_segments(segments, source_lang, args.target)

    if args.format == "vtt":
        subtitle_path = generate_vtt(translated, str(output_dir / "subtitles.vtt"))
    else:
        subtitle_path = generate_srt(translated, str(output_dir / "subtitles.srt"))
    log.record("subtitle_generation", "success", detail=str(subtitle_path))

    _print_stage("summarization")
    full_text = " ".join(seg["text"] for seg in transcript["segments"])
    summary_path = save_summary_output(full_text, str(output_dir / "summary.txt"))
    log.record("summarization", "success", detail=str(summary_path))

    return {
        "audio": audio_path,
        "transcript": transcript_path,
        "subtitles": subtitle_path,
        "summary": summary_path,
    }


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    log = ProcessingLog(args.output_dir)

    try:
        outputs = run_pipeline(args, log)
    except (InputValidationError, DownloadError, AudioExtractionError,
            TranscriptionError, TranslationError) as exc:
        log.record("pipeline", "failed", detail=str(exc))
        log.write()
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        log.record("pipeline", "failed", detail=str(exc))
        log.write()
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1

    log_path = log.write()

    print("\nPipeline completed successfully. Output files:")
    print(f"  Audio:     {outputs['audio']}")
    print(f"  Transcript: {outputs['transcript']}")
    print(f"  Subtitles:  {outputs['subtitles']}")
    print(f"  Summary:    {outputs['summary']}")
    print(f"  Log:        {log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
