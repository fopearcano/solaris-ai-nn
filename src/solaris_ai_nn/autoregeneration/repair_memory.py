"""Repair memory -- the audited record of every repair and its outcome.

Each :class:`RepairRecord` captures the degradation signal, the proposed and
applied (or refused) repair, the safety/governance decision, before/after
metrics, any rollback, and a result classification (improved / neutral /
harmful / inconclusive / rolled_back / refused). Persisted append-only.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .repair_actions import RepairResultClass


@dataclass
class RepairRecord:
    """One audited repair episode."""

    repair_id: str
    degradation_type: str = ""
    action_type: str = ""
    scope: str = ""
    applied: bool = False
    refused: bool = False
    refused_reason: str = ""
    rolled_back: bool = False
    result_class: str = RepairResultClass.INCONCLUSIVE
    before_metrics: Dict[str, Any] = field(default_factory=dict)
    after_metrics: Dict[str, Any] = field(default_factory=dict)
    safety_decision: str = ""
    governance_decision: str = ""
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.result_class not in RepairResultClass.ALL:
            self.result_class = RepairResultClass.INCONCLUSIVE

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class RepairMemory:
    """Bounded, persisted memory of repair episodes."""

    state_dir: Optional[Union[str, Path]] = None
    write_log: bool = True
    max_records: int = 2000
    records: List[RepairRecord] = field(default_factory=list)
    result_counts: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.log_path = (Path(self.state_dir) / "repair_memory.jsonl"
                         if self.state_dir else None)
        self.policy_state_path = (
            Path(self.state_dir) / "repair_policy_state.json"
            if self.state_dir else None)
        self.snapshots_dir = (Path(self.state_dir) / "repair_snapshots"
                              if self.state_dir else None)

    # -- recording ----------------------------------------------------------------

    def record(self, record: RepairRecord) -> RepairRecord:
        self.records.append(record)
        self.records = self.records[-self.max_records:]
        self.result_counts[record.result_class] = (
            self.result_counts.get(record.result_class, 0) + 1)
        if self.write_log and self.log_path is not None:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(record.to_dict(), default=str) + "\n")
        return record

    def save_policy_state(self, state: Dict[str, Any]) -> None:
        if self.policy_state_path is not None:
            self.policy_state_path.parent.mkdir(parents=True, exist_ok=True)
            self.policy_state_path.write_text(
                json.dumps(state, indent=2, default=str), encoding="utf-8")

    # -- views --------------------------------------------------------------------

    def applied_count(self) -> int:
        return sum(1 for r in self.records if r.applied)

    def refused_count(self) -> int:
        return self.result_counts.get(RepairResultClass.REFUSED, 0)

    def rollback_count(self) -> int:
        return self.result_counts.get(RepairResultClass.ROLLED_BACK, 0)

    def success_rate(self) -> Optional[float]:
        applied = [r for r in self.records if r.applied]
        if not applied:
            return None
        improved = sum(1 for r in applied
                       if r.result_class == RepairResultClass.IMPROVED)
        return round(improved / len(applied), 4)

    def harm_rate(self) -> Optional[float]:
        applied = [r for r in self.records if r.applied]
        if not applied:
            return None
        harmful = sum(1 for r in applied
                      if r.result_class == RepairResultClass.HARMFUL)
        return round(harmful / len(applied), 4)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "record_count": len(self.records),
            "result_counts": dict(self.result_counts),
            "applied_count": self.applied_count(),
            "refused_count": self.refused_count(),
            "rollback_count": self.rollback_count(),
            "success_rate": self.success_rate(),
            "harm_rate": self.harm_rate(),
            "log_path": str(self.log_path) if self.log_path else None,
            "recent": [r.to_dict() for r in self.records[-5:]],
        }
