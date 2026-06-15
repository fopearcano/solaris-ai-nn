"""Developmental memory -- append-only persistence across restarts.

The :class:`DevelopmentalMemoryStore` writes append-only JSONL records (life cycle,
epochs, growth state, maturation, phase transitions, plateaus, regressions).
Regressions, plateaus, failed transitions, and inconclusive results are all
preserved -- never deleted -- and state survives restart.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_FILES = {
    "life_cycle": "life_cycle.jsonl",
    "epoch": "epochs.jsonl",
    "growth_state": "growth_state.jsonl",
    "maturation": "maturation_markers.jsonl",
    "phase_transition": "phase_transitions.jsonl",
    "plateau": "plateaus.jsonl",
    "regression": "regressions.jsonl",
}


@dataclass
class DevelopmentalMemoryRecord:
    record_type: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"record_type": self.record_type, "timestamp": self.timestamp,
                "payload": self.payload}


@dataclass
class DevelopmentalIndex:
    counts: Dict[str, int] = field(default_factory=dict)
    epoch_ids: List[str] = field(default_factory=list)
    regression_count: int = 0
    plateau_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {"counts": dict(self.counts),
                "epoch_count": len(self.epoch_ids),
                "epoch_ids": list(self.epoch_ids),
                "regression_count": self.regression_count,
                "plateau_count": self.plateau_count}


@dataclass
class DevelopmentalMemoryStore:
    """Append-only developmental memory; regressions/plateaus preserved."""

    state_dir: str = ".solaris_ai_nn_development"
    index: DevelopmentalIndex = field(default_factory=DevelopmentalIndex)
    persist: bool = True

    def _append(self, record_type: str, payload: Dict[str, Any]) -> None:
        self.index.counts[record_type] = self.index.counts.get(
            record_type, 0) + 1
        if record_type == "epoch":
            eid = payload.get("epoch_id")
            if eid and eid not in self.index.epoch_ids:
                self.index.epoch_ids.append(eid)
        if record_type == "regression":
            self.index.regression_count += 1
        if record_type == "plateau":
            self.index.plateau_count += 1
        if not self.persist:
            return
        filename = _FILES.get(record_type)
        if filename is None:
            return
        os.makedirs(self.state_dir, exist_ok=True)
        with open(os.path.join(self.state_dir, filename), "a",
                  encoding="utf-8") as fh:
            fh.write(json.dumps(
                DevelopmentalMemoryRecord(record_type, payload).to_dict(),
                default=str) + "\n")

    def record_life_cycle(self, payload: Dict[str, Any]) -> None:
        self._append("life_cycle", payload)

    def record_epoch(self, payload: Dict[str, Any]) -> None:
        self._append("epoch", payload)

    def record_growth_state(self, payload: Dict[str, Any]) -> None:
        self._append("growth_state", payload)

    def record_maturation(self, payload: Dict[str, Any]) -> None:
        self._append("maturation", payload)

    def record_phase_transition(self, payload: Dict[str, Any]) -> None:
        self._append("phase_transition", payload)

    def record_plateau(self, payload: Dict[str, Any]) -> None:
        self._append("plateau", payload)

    def record_regression(self, payload: Dict[str, Any]) -> None:
        self._append("regression", payload)

    def write_index(self) -> Optional[str]:
        if not self.persist:
            return None
        os.makedirs(self.state_dir, exist_ok=True)
        path = os.path.join(self.state_dir, "developmental_index.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.index.to_dict(), fh, indent=2, default=str)
        return path

    def read_records(self, record_type: str) -> List[Dict[str, Any]]:
        filename = _FILES.get(record_type)
        if filename is None:
            return []
        path = os.path.join(self.state_dir, filename)
        if not os.path.isfile(path):
            return []
        out: List[Dict[str, Any]] = []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def load_index(self) -> DevelopmentalIndex:
        """Reload the index from disk (state survives restart)."""
        path = os.path.join(self.state_dir, "developmental_index.json")
        if not os.path.isfile(path):
            return self.index
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        self.index = DevelopmentalIndex(
            counts=dict(data.get("counts", {})),
            epoch_ids=list(data.get("epoch_ids", [])),
            regression_count=int(data.get("regression_count", 0)),
            plateau_count=int(data.get("plateau_count", 0)))
        return self.index

    def snapshot(self) -> Dict[str, Any]:
        return self.index.to_dict()
