"""ReadOnlyStreamIngestor -- reads local streams; never anything else.

Hard rules, enforced structurally (there is simply no code for the
alternatives): only files explicitly passed by the operator are opened, only
for reading; nothing is written, deleted, executed, or followed; directory
ingestion is a non-recursive glob; tailing is bounded by lines and/or
duration. Every rejected line is counted and remembered with its reason.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

from ..utils.logging import get_logger
from . import data_contracts as DC

logger = get_logger(__name__)


@dataclass
class ReadOnlyStreamIngestor:
    """Turns local JSONL/text files into canonical sensory events."""

    default_intensity: float = 0.5
    max_errors_kept: int = 50

    lines_read: int = field(default=0, init=False)
    events_accepted: int = field(default=0, init=False)
    events_rejected: int = field(default=0, init=False)
    files_read: List[str] = field(default_factory=list, init=False)
    errors: List[Dict[str, Any]] = field(default_factory=list, init=False)

    # -- format handling ------------------------------------------------------

    @staticmethod
    def detect_format(path: Union[str, Path]) -> str:
        return "jsonl" if str(path).endswith((".jsonl", ".ndjson")) else "text"

    def _record_error(self, path: str, line_no: int, reasons: List[str],
                      line: str = "") -> None:
        self.events_rejected += 1
        self.errors.append({
            "path": path, "line": line_no, "reasons": list(reasons),
            "preview": line[:80],
        })
        self.errors = self.errors[-self.max_errors_kept:]

    def _validate_line(self, raw: str, fmt: str,
                       source: str) -> Optional[Dict[str, Any]]:
        """One raw line -> normalized event dict, or None if rejected."""
        if fmt == "jsonl":
            if not raw.strip():
                return None  # blank JSONL lines are skipped silently
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                self._record_error(source, self.lines_read,
                                   [f"malformed JSON: {exc}"], raw)
                return None
            result = DC.validate_jsonl_event(data)
        else:
            result = DC.validate_text_line(
                raw, source=source, default_intensity=self.default_intensity)
            if not result.valid and result.reasons \
                    and "blank line" in result.reasons[0]:
                return None  # blank text lines are skipped, not errors
        if not result.valid:
            self._record_error(source, self.lines_read, result.reasons, raw)
            return None
        self.events_accepted += 1
        return result.normalized

    # -- reading ---------------------------------------------------------------

    def read_once(self, path: Union[str, Path],
                  fmt: Optional[str] = None) -> List[Dict[str, Any]]:
        """Read one explicitly-named file completely; return accepted events."""
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(f"input file not found: {path}")
        fmt = fmt or self.detect_format(path)
        events: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for raw in fh:
                self.lines_read += 1
                event = self._validate_line(raw, fmt, str(path.name))
                if event is not None:
                    events.append(event)
        self.files_read.append(str(path))
        return events

    def tail_bounded(self, path: Union[str, Path],
                     max_lines: Optional[int] = None,
                     max_duration_s: Optional[float] = None,
                     poll_interval_s: float = 0.05,
                     fmt: Optional[str] = None,
                     from_start: bool = True,
                     ) -> Iterator[Dict[str, Any]]:
        """Yield events from a (possibly growing) file, strictly bounded.

        At least one of ``max_lines`` / ``max_duration_s`` is required --
        there is no unbounded tail.
        """
        if max_lines is None and max_duration_s is None:
            raise ValueError("tail_bounded requires max_lines and/or "
                             "max_duration_s -- tailing is never unbounded")
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(f"input file not found: {path}")
        fmt = fmt or self.detect_format(path)
        deadline = (time.monotonic() + max_duration_s
                    if max_duration_s is not None else None)
        yielded = 0
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            if not from_start:
                fh.seek(0, 2)  # start at the current end
            while True:
                if max_lines is not None and yielded >= max_lines:
                    break
                if deadline is not None and time.monotonic() >= deadline:
                    break
                raw = fh.readline()
                if not raw:
                    if deadline is None:
                        break  # bounded by lines only: EOF ends the tail
                    time.sleep(poll_interval_s)
                    continue
                self.lines_read += 1
                event = self._validate_line(raw, fmt, str(path.name))
                if event is not None:
                    yielded += 1
                    yield event
        if str(path) not in self.files_read:
            self.files_read.append(str(path))

    def ingest_directory(self, path: Union[str, Path],
                         pattern: str = "*.jsonl",
                         max_files: Optional[int] = None,
                         ) -> List[Dict[str, Any]]:
        """Read matching files in ONE directory (non-recursive by design)."""
        directory = Path(path)
        if not directory.is_dir():
            raise NotADirectoryError(f"not a directory: {directory}")
        if "**" in pattern:
            raise ValueError("recursive patterns are not allowed; pass each "
                             "directory explicitly")
        files = sorted(p for p in directory.glob(pattern) if p.is_file())
        if max_files is not None:
            files = files[:max_files]
        events: List[Dict[str, Any]] = []
        for file_path in files:
            events.extend(self.read_once(file_path))
        return events

    # -- status -----------------------------------------------------------------

    def validity_rate(self) -> float:
        total = self.events_accepted + self.events_rejected
        return (self.events_accepted / total) if total else 1.0

    def snapshot(self) -> Dict[str, Any]:
        return {
            "lines_read": self.lines_read,
            "events_accepted": self.events_accepted,
            "events_rejected": self.events_rejected,
            "validity_rate": round(self.validity_rate(), 4),
            "files_read": list(self.files_read),
            "recent_errors": self.errors[-5:],
            "read_only": True,  # structurally: this class only ever reads
        }
