"""Exploration memory -- the record of what sampling actually helped.

Each :class:`ExplorationRecord` captures the action, the context before, the
result after, expected vs observed information gain, before/after Mysterium /
prediction / world-model / proto-symbol metrics, cost, safety status, and an
outcome classification (useful / neutral / harmful / unknown / blocked). The
store appends to ``exploration_memory.jsonl`` and can persist a compact
snapshot. Bounded in memory.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class ExplorationOutcome:
    USEFUL = "useful"
    NEUTRAL = "neutral"
    HARMFUL = "harmful"
    UNKNOWN = "unknown"
    BLOCKED = "blocked"

    ALL = (USEFUL, NEUTRAL, HARMFUL, UNKNOWN, BLOCKED)


@dataclass
class ExplorationRecord:
    """One sampling episode, fully accounted for."""

    action_id: str
    action_type: str
    scope: str = ""
    source_pressure: str = ""
    expected_information_gain: float = 0.0
    observed_information_gain: float = 0.0
    cost: float = 0.0
    mysterium_before: Optional[float] = None
    mysterium_after: Optional[float] = None
    prediction_accuracy_before: Optional[float] = None
    prediction_accuracy_after: Optional[float] = None
    world_model_confidence_before: Optional[float] = None
    world_model_confidence_after: Optional[float] = None
    proto_symbol_ambiguity_before: Optional[float] = None
    proto_symbol_ambiguity_after: Optional[float] = None
    safety_status: str = "ok"
    outcome: str = ExplorationOutcome.UNKNOWN
    step: int = 0
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.outcome not in ExplorationOutcome.ALL:
            self.outcome = ExplorationOutcome.UNKNOWN

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ExplorationMemory:
    """Bounded, persisted history of sampling outcomes."""

    state_dir: Optional[Union[str, Path]] = None
    write_log: bool = True
    max_records: int = 1000
    records: List[ExplorationRecord] = field(default_factory=list)
    outcome_counts: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.log_path = (Path(self.state_dir) / "exploration_memory.jsonl"
                         if self.state_dir else None)
        self.policy_state_path = (
            Path(self.state_dir) / "sampling_policy_state.json"
            if self.state_dir else None)
        self.attention_state_path = (
            Path(self.state_dir) / "attention_state.json"
            if self.state_dir else None)

    # -- recording ----------------------------------------------------------------

    def record(self, record: ExplorationRecord) -> ExplorationRecord:
        self.records.append(record)
        self.records = self.records[-self.max_records:]
        self.outcome_counts[record.outcome] = (
            self.outcome_counts.get(record.outcome, 0) + 1)
        if self.write_log and self.log_path is not None:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(record.to_dict(), default=str) + "\n")
        return record

    def useful_rate(self) -> float:
        total = sum(self.outcome_counts.values())
        if not total:
            return 0.0
        return round(self.outcome_counts.get(ExplorationOutcome.USEFUL, 0)
                     / total, 4)

    def blocked_count(self) -> int:
        return self.outcome_counts.get(ExplorationOutcome.BLOCKED, 0)

    # -- persistence --------------------------------------------------------------

    def save_policy_state(self, state: Dict[str, Any]) -> None:
        if self.policy_state_path is not None:
            self.policy_state_path.parent.mkdir(parents=True, exist_ok=True)
            self.policy_state_path.write_text(
                json.dumps(state, indent=2, default=str), encoding="utf-8")

    def save_attention_state(self, state: Dict[str, Any]) -> None:
        if self.attention_state_path is not None:
            self.attention_state_path.parent.mkdir(parents=True,
                                                   exist_ok=True)
            self.attention_state_path.write_text(
                json.dumps(state, indent=2, default=str), encoding="utf-8")

    # -- views --------------------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        return {
            "record_count": len(self.records),
            "outcome_counts": dict(self.outcome_counts),
            "useful_rate": self.useful_rate(),
            "blocked_count": self.blocked_count(),
            "log_path": str(self.log_path) if self.log_path else None,
            "recent": [r.to_dict() for r in self.records[-5:]],
        }
