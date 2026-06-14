"""Post-pilot artifact loader -- read run artifacts without mutating them.

The :class:`PilotArtifactLoader` reads the Pilot-1 and runtime-state artifacts
into a :class:`PilotArtifactSet`. Missing optional artifacts are *reported*,
never fatal; corrupted artifacts are quarantined and marked unreadable; and
the loader never mutates source artifacts (it only optionally writes an index).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Artifact name -> (relative path under base, json|jsonl, dir|file).
_PILOT_ARTIFACTS = {
    "observability": ("observability.jsonl", "jsonl", "file"),
    "metrics_daily": ("metrics_daily.jsonl", "jsonl", "file"),
    "incidents": ("incidents.jsonl", "jsonl", "file"),
    "dashboard": ("dashboard.json", "json", "file"),
    "pilot_report": ("PILOT_REPORT.json", "json", "file"),
    "daily": ("daily", "json", "dir"),
    "weekly": ("weekly", "json", "dir"),
}
_STATE_ARTIFACTS = {
    "developmental_state": ("developmental_state.json", "json", "file"),
    "developmental_epochs": ("developmental_epochs.jsonl", "jsonl", "file"),
    "autobiographical_memory": ("autobiographical_memory.jsonl", "jsonl",
                                "file"),
    "proto_symbols": ("proto_symbols.json", "json", "file"),
    "symbol_memory": ("symbol_memory.jsonl", "jsonl", "file"),
    "hypotheses": ("hypotheses.json", "json", "file"),
    "hypothesis_history": ("hypothesis_history.jsonl", "jsonl", "file"),
    "logos_tensions": ("logos_tensions.jsonl", "jsonl", "file"),
    "repair_memory": ("repair_memory.jsonl", "jsonl", "file"),
    "conscience_bus": ("conscience_bus.jsonl", "jsonl", "file"),
}


@dataclass
class ArtifactIndex:
    """An inventory of which artifacts were present, missing, or unreadable."""

    present: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)
    unreadable: List[str] = field(default_factory=list)
    paths: Dict[str, str] = field(default_factory=dict)
    sizes: Dict[str, int] = field(default_factory=dict)

    @property
    def completeness(self) -> float:
        total = len(self.present) + len(self.missing) + len(self.unreadable)
        return round(len(self.present) / total, 4) if total else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__), "completeness": self.completeness}


@dataclass
class PilotArtifactSet:
    """The loaded (read-only) artifacts of one pilot run."""

    base_dir: str
    state_dir: str
    data: Dict[str, Any] = field(default_factory=dict)
    index: ArtifactIndex = field(default_factory=ArtifactIndex)

    def get(self, name: str, default: Any = None) -> Any:
        return self.data.get(name, default)

    def has(self, name: str) -> bool:
        return name in self.data

    @property
    def completeness(self) -> float:
        return self.index.completeness

    def to_dict(self) -> Dict[str, Any]:
        return {"base_dir": self.base_dir, "state_dir": self.state_dir,
                "index": self.index.to_dict(),
                "loaded": sorted(self.data)}


@dataclass
class PilotArtifactLoader:
    """Loads pilot + state artifacts read-only, reporting gaps and corruption."""

    base_dir: str = ".solaris_ai_nn_pilot1"
    state_dir: str = ".solaris_ai_nn_state"

    def load(self) -> PilotArtifactSet:
        artifacts = PilotArtifactSet(base_dir=self.base_dir,
                                     state_dir=self.state_dir)
        for name, (rel, fmt, kind) in _PILOT_ARTIFACTS.items():
            self._load_one(artifacts, name, self.base_dir, rel, fmt, kind)
        for name, (rel, fmt, kind) in _STATE_ARTIFACTS.items():
            self._load_one(artifacts, name, self.state_dir, rel, fmt, kind)
        return artifacts

    def _load_one(self, artifacts: PilotArtifactSet, name: str, base: str,
                  rel: str, fmt: str, kind: str) -> None:
        path = os.path.join(base, rel)
        idx = artifacts.index
        if kind == "dir":
            if not os.path.isdir(path):
                idx.missing.append(name)
                return
            records, unreadable = self._read_dir(path)
            if records is None:
                idx.unreadable.append(name)
                return
            artifacts.data[name] = records
            idx.present.append(name)
            idx.paths[name] = path
            idx.sizes[name] = len(records)
            return
        if not os.path.isfile(path):
            idx.missing.append(name)
            return
        try:
            if fmt == "jsonl":
                value = self._read_jsonl(path)
            else:
                with open(path, encoding="utf-8") as fh:
                    value = json.load(fh)
        except Exception:
            # Corrupted: quarantine by marking unreadable; never mutate source.
            idx.unreadable.append(name)
            return
        artifacts.data[name] = value
        idx.present.append(name)
        idx.paths[name] = path
        idx.sizes[name] = (len(value) if isinstance(value, (list, dict))
                           else 1)

    @staticmethod
    def _read_jsonl(path: str) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                out.append(json.loads(line))  # a bad line raises -> unreadable
        return out

    @staticmethod
    def _read_dir(path: str) -> "tuple[Optional[List[Dict[str, Any]]], bool]":
        records: List[Dict[str, Any]] = []
        any_bad = False
        for name in sorted(os.listdir(path)):
            if not name.endswith(".json"):
                continue
            try:
                with open(os.path.join(path, name), encoding="utf-8") as fh:
                    records.append(json.load(fh))
            except Exception:
                any_bad = True
                continue
        return records, any_bad

    def write_index(self, artifacts: PilotArtifactSet,
                    out_dir: Optional[str] = None) -> str:
        """Optionally persist the artifact index (the only thing we write)."""
        out_dir = out_dir or self.base_dir
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, "artifact_index.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(artifacts.index.to_dict(), fh, indent=2, default=str)
        return path
