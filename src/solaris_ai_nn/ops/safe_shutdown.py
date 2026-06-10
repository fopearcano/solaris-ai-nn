"""SafeShutdownManager -- dying well is part of continuity.

A safe shutdown checkpoints first, records *why* it stopped, writes the final
health report / Inner MAP snapshot / session report where available, and marks
the manifest graceful — so the next session restores cleanly with a full
account of how the last one ended.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Union


@dataclass
class SafeShutdownManager:
    """Coordinates the graceful end of a supervised run."""

    ops_dir: Union[str, Path]
    run_id: str = ""
    session_id: str = ""

    _requested: bool = field(default=False, init=False)
    _reason: Optional[str] = field(default=None, init=False)
    _performed: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        self.ops_dir = Path(self.ops_dir)
        self.ops_dir.mkdir(parents=True, exist_ok=True)

    def request_shutdown(self, reason: str) -> None:
        """Record the request; the supervisor acts on it at the next boundary."""
        self._requested = True
        self._reason = reason

    @property
    def requested(self) -> bool:
        return self._requested

    def perform_shutdown(self, runner: Any = None,
                         health_report: Optional[Dict[str, Any]] = None,
                         inner_map: Optional[Dict[str, Any]] = None,
                         final_report_md: Optional[str] = None) -> Dict[str, Any]:
        """Stop the runner (if it supports stop), then write the evidence."""
        reason = self._reason or "shutdown requested"
        if runner is not None and callable(getattr(runner, "stop", None)):
            try:
                runner.stop(reason)
            except Exception as exc:  # record, never block the shutdown
                reason += f" (runner.stop raised: {exc})"

        record = {
            "run_id": self.run_id, "session_id": self.session_id,
            "reason": reason, "timestamp": time.time(), "graceful": True,
        }
        self._write_json(self.ops_dir / "shutdown.json", record)
        if health_report is not None:
            self._write_json(self.ops_dir / "final_health.json", health_report)
        if inner_map is not None:
            self._write_json(self.ops_dir / "final_inner_map.json", inner_map)
        if final_report_md is not None:
            (self.ops_dir / "final_report.md").write_text(
                final_report_md, encoding="utf-8")
        self._performed = True
        return record

    @staticmethod
    def _write_json(path: Path, data: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, default=str)

    def snapshot(self) -> Dict[str, Any]:
        return {"requested": self._requested, "reason": self._reason,
                "performed": self._performed, "ops_dir": str(self.ops_dir)}
