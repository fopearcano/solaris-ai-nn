"""Need memory -- the durable trail of pressure, conflict, and tension.

Need/drive/desire/conflict/valence/auto-determination state over time, as
append-only JSONL plus the latest snapshots as JSON:

* ``need_trace.jsonl``          -- one row per regulation update
* ``homeostasis_state.json``    -- the latest full snapshot
* ``auto_determination.json``   -- the latest Being/Not-Being state
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


@dataclass
class NeedTrace:
    """One regulation update, summarized for the trail."""

    step: int = 0
    dominant_need: Optional[str] = None
    dominant_drive: Optional[str] = None
    need_count: int = 0
    conflict_count: int = 0
    suppressed_desires: int = 0
    best_desire: Optional[str] = None
    valence_rolling: float = 0.0
    being_pressure: float = 0.0
    not_being_pressure: float = 0.0
    tension: float = 0.0
    action_implication: str = "no_action"
    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class NeedMemory:
    """Persistence for the homeostasis layer, under the state dir."""

    state_dir: Union[str, Path] = ".solaris_ai_nn_state"

    def __post_init__(self) -> None:
        self.state_dir = Path(self.state_dir)
        self.need_trace_path = self.state_dir / "need_trace.jsonl"
        self.state_path = self.state_dir / "homeostasis_state.json"
        self.auto_determination_path = (self.state_dir
                                        / "auto_determination.json")
        self.rows_written = 0

    def record(self, trace: NeedTrace) -> NeedTrace:
        self.need_trace_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.need_trace_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(trace.to_dict(), default=str) + "\n")
        self.rows_written += 1
        return trace

    def save_state(self, snapshot: Dict[str, Any]) -> Path:
        return self._write(self.state_path, snapshot)

    def save_auto_determination(self, snapshot: Dict[str, Any]) -> Path:
        return self._write(self.auto_determination_path, snapshot)

    @staticmethod
    def _write(path: Path, data: Dict[str, Any]) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, default=str)
        return path

    def load_state(self) -> Optional[Dict[str, Any]]:
        if not self.state_path.exists():
            return None
        with open(self.state_path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    def traces(self) -> List[Dict[str, Any]]:
        if not self.need_trace_path.exists():
            return []
        rows = []
        with open(self.need_trace_path, "r", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    rows.append(json.loads(line))
        return rows

    def snapshot(self) -> Dict[str, Any]:
        return {
            "rows_written": self.rows_written,
            "trace_rows_on_disk": len(self.traces()),
            "paths": {
                "need_trace": str(self.need_trace_path),
                "homeostasis_state": str(self.state_path),
                "auto_determination": str(self.auto_determination_path),
            },
        }
