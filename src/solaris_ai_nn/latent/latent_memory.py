"""Latent memory -- the durable record of what offline processing did.

Every replay window, dream/counterfactual simulation, and consolidated schema
is written down, always marked ``offline=True``. Files live under the state
directory:

* ``latent_memory.jsonl``       -- one row per latent cycle
* ``dream_traces.jsonl``        -- one row per sandboxed simulation
* ``replay_traces.jsonl``       -- one row per replayed window
* ``consolidated_schemas.json`` -- the current schema set
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


@dataclass
class LatentMemoryRecord:
    """One latent cycle, summarized."""

    cycle_type: str  # sleep | consolidation | replay | dream
    steps_run: int = 0
    replayed_window_ids: List[str] = field(default_factory=list)
    counterfactual_kinds: List[str] = field(default_factory=list)
    substrate_response: Dict[str, Any] = field(default_factory=dict)
    prediction_results: Dict[str, Any] = field(default_factory=dict)
    mysterium_change: float = 0.0
    schema_summaries: List[str] = field(default_factory=list)
    offline_suggestions: List[Dict[str, Any]] = field(default_factory=list)
    production_mutated: bool = False
    offline: bool = True  # structurally: latent output is offline output
    cycle_id: str = field(default_factory=_new_id)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ReplayTrace:
    """One replayed window: what went in, what the sandbox did."""

    window_id: str
    strategy: str
    events_replayed: int = 0
    before: Dict[str, Any] = field(default_factory=dict)
    after: Dict[str, Any] = field(default_factory=dict)
    comparison: Dict[str, Any] = field(default_factory=dict)
    seed: int = 0
    mutated_production: bool = False
    offline: bool = True
    replay_id: str = field(default_factory=_new_id)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class DreamTrace:
    """One sandboxed counterfactual simulation. Offline, always."""

    window_id: str
    counterfactual_kind: str
    counterfactual_id: str = ""
    events_replayed: int = 0
    divergence: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    offline: bool = True
    simulated: bool = True
    dream_id: str = field(default_factory=_new_id)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ConsolidatedSchema:
    """A stable pattern distilled from the trace during consolidation."""

    pattern: str
    dominant_action: Optional[str] = None
    support_count: int = 0
    average_valence: Optional[float] = None
    source: str = "consolidation"
    schema_id: str = field(default_factory=_new_id)
    updated_at: float = field(default_factory=time.time)

    def summary(self) -> str:
        valence = (f"{self.average_valence:+.2f}"
                   if self.average_valence is not None else "n/a")
        return (f"pattern {self.pattern!r} -> {self.dominant_action!r} "
                f"(support {self.support_count}, valence {valence})")

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class LatentMemoryStore:
    """Append-only persistence for latent evidence under the state dir."""

    state_dir: Union[str, Path] = ".solaris_ai_nn_state"

    def __post_init__(self) -> None:
        self.state_dir = Path(self.state_dir)
        self.latent_memory_path = self.state_dir / "latent_memory.jsonl"
        self.dream_traces_path = self.state_dir / "dream_traces.jsonl"
        self.replay_traces_path = self.state_dir / "replay_traces.jsonl"
        self.schemas_path = self.state_dir / "consolidated_schemas.json"
        self._schemas: Dict[str, ConsolidatedSchema] = {}
        self._load_schemas()

    # -- appends ---------------------------------------------------------------

    def _append(self, path: Path, row: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, default=str) + "\n")

    def record_cycle(self, record: LatentMemoryRecord) -> LatentMemoryRecord:
        self._append(self.latent_memory_path, record.to_dict())
        return record

    def record_replay(self, trace: ReplayTrace) -> ReplayTrace:
        self._append(self.replay_traces_path, trace.to_dict())
        return trace

    def record_dream(self, trace: DreamTrace) -> DreamTrace:
        self._append(self.dream_traces_path, trace.to_dict())
        return trace

    # -- schemas -----------------------------------------------------------------

    def upsert_schema(self, schema: ConsolidatedSchema) -> ConsolidatedSchema:
        """Insert or refresh a schema keyed by its pattern."""
        existing = self._schemas.get(schema.pattern)
        if existing is not None:
            schema.schema_id = existing.schema_id
        self._schemas[schema.pattern] = schema
        self._save_schemas()
        return schema

    def schemas(self) -> List[ConsolidatedSchema]:
        return list(self._schemas.values())

    def _save_schemas(self) -> None:
        self.schemas_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.schemas_path, "w", encoding="utf-8") as fh:
            json.dump({"schemas": [s.to_dict()
                                   for s in self._schemas.values()]},
                      fh, indent=2, default=str)

    def _load_schemas(self) -> None:
        if not self.schemas_path.exists():
            return
        with open(self.schemas_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        for row in data.get("schemas", []):
            valid = {k: v for k, v in row.items()
                     if k in ConsolidatedSchema.__dataclass_fields__}  # type: ignore[attr-defined]
            schema = ConsolidatedSchema(**valid)
            self._schemas[schema.pattern] = schema

    # -- reads / status --------------------------------------------------------------

    @staticmethod
    def _read(path: Path) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        rows = []
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    rows.append(json.loads(line))
        return rows

    def cycles(self) -> List[Dict[str, Any]]:
        return self._read(self.latent_memory_path)

    def replays(self) -> List[Dict[str, Any]]:
        return self._read(self.replay_traces_path)

    def dreams(self) -> List[Dict[str, Any]]:
        return self._read(self.dream_traces_path)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "cycle_count": len(self.cycles()),
            "replay_count": len(self.replays()),
            "dream_count": len(self.dreams()),
            "schema_count": len(self._schemas),
            "paths": {
                "latent_memory": str(self.latent_memory_path),
                "dream_traces": str(self.dream_traces_path),
                "replay_traces": str(self.replay_traces_path),
                "consolidated_schemas": str(self.schemas_path),
            },
        }
