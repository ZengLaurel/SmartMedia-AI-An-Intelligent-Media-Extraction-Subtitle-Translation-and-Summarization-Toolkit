"""Shared processing pipeline for command-line and desktop interfaces."""

from dataclasses import dataclass, field
from pathlib import Path
from threading import Event
from typing import Callable

import config
from ai_engine import transcribe_audio, transcribe_long_audio
from downloader import download_from_url, import_local_file
from media_processor import extract_audio, get_audio_duration
from subtitle_generator import generate_srt, generate_vtt, segment_transcript, translate_segments
from summarizer import save_summary_output
from utils import ProcessingLog

SUBTITLE_FORMATS = ("srt", "vtt")


@dataclass(frozen=True)
class PipelineOptions:
    file: str | None = None
    url: str | None = None
    source: str | None = None
    target: str = "zh"
    format: str = "srt"
    output_dir: str = field(default_factory=lambda: config.OUTPUT_DIR)


class PipelineCancelled(Exception):
    pass


class PipelineLogError(RuntimeError):
    pass


def run_pipeline(
    options: PipelineOptions,
    on_progress: Callable[[str], None] | None = None,
    cancel_event: Event | None = None,
) -> dict[str, Path]:
    log = ProcessingLog(options.output_dir)
    current_stage = "input"
    failure = None

    def check_cancelled():
        if cancel_event is not None and cancel_event.is_set():
            raise PipelineCancelled("Processing cancelled.")

    def start_stage(stage):
        nonlocal current_stage
        check_cancelled()
        current_stage = stage
        log.record(stage, "starting")
        if on_progress is not None:
            on_progress(stage)
        check_cancelled()

    try:
        check_cancelled()
        if bool(options.file) == bool(options.url):
            raise ValueError("Choose exactly one local file or URL.")
        if options.format not in SUBTITLE_FORMATS:
            raise ValueError("Subtitle format must be srt or vtt.")
        output_dir = Path(options.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if options.url:
            start_stage("download")
            media_path = download_from_url(options.url, output_dir=str(output_dir))
            log.record("download", "success", detail=str(media_path))
        else:
            start_stage("import")
            media_path = import_local_file(options.file)
            log.record("import", "success", detail=str(media_path))

        start_stage("extraction")
        audio_path = extract_audio(str(media_path), str(output_dir / "audio.wav"))
        log.record("extraction", "success", detail=str(audio_path))

        start_stage("transcription")
        duration = get_audio_duration(str(audio_path))
        check_cancelled()
        if duration > config.MAX_AUDIO_SEGMENT_SECONDS:
            transcript = transcribe_long_audio(
                str(audio_path),
                segment_seconds=config.MAX_AUDIO_SEGMENT_SECONDS,
                temp_dir=str(output_dir / "chunks"),
                language=options.source,
            )
        else:
            transcript = transcribe_audio(str(audio_path), language=options.source)
        log.record("transcription", "success", detail=f"{len(transcript['segments'])} segments")
        check_cancelled()

        transcript_path = output_dir / "transcript.txt"
        transcript_path.write_text(
            "\n".join(seg["text"] for seg in transcript["segments"]), encoding="utf-8"
        )

        start_stage("subtitle generation")
        segments = segment_transcript(transcript)
        translated = translate_segments(segments, options.source or transcript["language"], options.target)
        check_cancelled()
        if options.format == "vtt":
            subtitle_path = generate_vtt(translated, str(output_dir / "subtitles.vtt"))
        else:
            subtitle_path = generate_srt(translated, str(output_dir / "subtitles.srt"))
        log.record("subtitle_generation", "success", detail=str(subtitle_path))

        start_stage("summarization")
        full_text = " ".join(seg["text"] for seg in transcript["segments"])
        summary_path = save_summary_output(full_text, str(output_dir / "summary.txt"))
        log.record("summarization", "success", detail=str(summary_path))
        check_cancelled()
        outputs = {
            "audio": audio_path,
            "transcript": transcript_path,
            "subtitles": subtitle_path,
            "summary": summary_path,
        }
    except PipelineCancelled as exc:
        failure = exc
        log.record(current_stage, "cancelled")
        log.record("pipeline", "cancelled")
        raise
    except Exception as exc:
        failure = exc
        log.record(current_stage, "failed", detail=str(exc))
        log.record("pipeline", "failed", detail=str(exc))
        raise
    finally:
        try:
            log_path = log.write()
        except OSError as exc:
            if failure is None:
                message = "Processing finished, but the log could not be saved"
            else:
                message = str(failure)
            raise PipelineLogError(f"{message}; log write failed: {exc}") from exc

    return {**outputs, "log": log_path}
