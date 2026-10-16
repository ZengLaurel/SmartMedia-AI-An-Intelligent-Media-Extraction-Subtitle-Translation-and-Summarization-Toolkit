"""Shared utility helpers."""

from datetime import datetime, timezone
from pathlib import Path


class ProcessingLog:
    """Accumulates timestamped stage/status entries for one pipeline run and
    writes them to a log file in the output directory on every run,
    whether it succeeds or fails (FR-40).
    """

    def __init__(self, output_dir: str, filename: str = "processing.log"):
        self.output_dir = Path(output_dir)
        self.filename = filename
        self._entries: list[str] = []

    def record(self, stage: str, status: str, detail: str = "") -> None:
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        line = f"[{timestamp}] stage={stage} status={status}"
        if detail:
            line += f" detail={detail}"
        self._entries.append(line)

    def write(self) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        log_path = self.output_dir / self.filename
        log_path.write_text("\n".join(self._entries) + "\n", encoding="utf-8")
        return log_path

