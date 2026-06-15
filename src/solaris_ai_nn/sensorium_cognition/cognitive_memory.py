"""Cognitive memory -- append-only persistence of cognitive traces.

The :class:`CognitiveMemoryStore` writes append-only JSONL records (moves,
predictions, anticipations, questions, simulations, synthesis). Failed predictions,
failed simulations, ambiguity, and other negative results are preserved -- never
deleted.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

_FILES = {
    "move": "cognitive_moves.jsonl",
    "prediction": "predictions.jsonl",
    "anticipation": "anticipations.jsonl",
    "question": "questions.jsonl",
    "simulation": "simulations.jsonl",
    "synthesis": "synthesis.jsonl",
}


@dataclass
class CognitiveMemoryRecord:
    record_type: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {"record_type": self.record_type, "timestamp": self.timestamp,
                "payload": self.payload}


@dataclass
class CognitiveTraceIndex:
    counts: Dict[str, int] = field(default_factory=dict)
    failed_prediction_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"counts": dict(self.counts),
                "failed_prediction_count": len(self.failed_prediction_ids),
                "failed_prediction_ids": list(self.failed_prediction_ids)}


@dataclass
class CognitiveMemoryStore:
    """Append-only store for cognitive traces (negative results preserved)."""

    state_dir: str = ".solaris_ai_nn_cognition"
    index: CognitiveTraceIndex = field(default_factory=CognitiveTraceIndex)
    persist: bool = True

    def _path(self, name: str) -> str:
        return os.path.join(self.state_dir, name)

    def _append(self, record_type: str, payload: Dict[str, Any]) -> None:
        self.index.counts[record_type] = self.index.counts.get(
            record_type, 0) + 1
        if record_type == "prediction" and payload.get("outcome") == "failure":
            pid = payload.get("prediction_id")
            if pid:
                self.index.failed_prediction_ids.append(pid)
        if not self.persist:
            return
        filename = _FILES.get(record_type)
        if filename is None:
            return
        os.makedirs(self.state_dir, exist_ok=True)
        with open(self._path(filename), "a", encoding="utf-8") as fh:
            fh.write(json.dumps(
                CognitiveMemoryRecord(record_type, payload).to_dict(),
                default=str) + "\n")

    def record_move(self, payload: Dict[str, Any]) -> None:
        self._append("move", payload)

    def record_prediction(self, payload: Dict[str, Any]) -> None:
        self._append("prediction", payload)

    def record_anticipation(self, payload: Dict[str, Any]) -> None:
        self._append("anticipation", payload)

    def record_question(self, payload: Dict[str, Any]) -> None:
        self._append("question", payload)

    def record_simulation(self, payload: Dict[str, Any]) -> None:
        self._append("simulation", payload)

    def record_synthesis(self, payload: Dict[str, Any]) -> None:
        self._append("synthesis", payload)

    def write_index(self) -> Optional[str]:
        if not self.persist:
            return None
        os.makedirs(self.state_dir, exist_ok=True)
        path = self._path("cognitive_index.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.index.to_dict(), fh, indent=2, default=str)
        return path

    def read_records(self, record_type: str) -> List[Dict[str, Any]]:
        filename = _FILES.get(record_type)
        if filename is None:
            return []
        path = self._path(filename)
        if not os.path.isfile(path):
            return []
        out: List[Dict[str, Any]] = []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def snapshot(self) -> Dict[str, Any]:
        return self.index.to_dict()
