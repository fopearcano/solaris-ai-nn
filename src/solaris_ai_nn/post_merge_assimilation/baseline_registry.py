"""Baseline registry -- the append-only ledger of experimental baselines.

:class:`BaselineRegistry` records each post-merge candidate baseline and its
evidence index. It is append-only: status changes add new history entries, old
baselines are never deleted, and failed/blocked baselines remain visible.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class BaselineStatus:
    CANDIDATE = "candidate"
    VALIDATED = "validated"
    VALIDATED_WITH_WARNINGS = "validated_with_warnings"
    REGRESSION_WATCH = "regression_watch"
    BLOCKED_BY_SAFETY = "blocked_by_safety"
    BLOCKED_BY_TESTS = "blocked_by_tests"
    BLOCKED_BY_FALSIFICATION = "blocked_by_falsification"
    ROLLBACK_RECOMMENDED = "rollback_recommended"
    ARCHIVED = "archived"
    UNKNOWN = "unknown"

    ALL = (CANDIDATE, VALIDATED, VALIDATED_WITH_WARNINGS, REGRESSION_WATCH,
           BLOCKED_BY_SAFETY, BLOCKED_BY_TESTS, BLOCKED_BY_FALSIFICATION,
           ROLLBACK_RECOMMENDED, ARCHIVED, UNKNOWN)

    BLOCKED = (BLOCKED_BY_SAFETY, BLOCKED_BY_TESTS, BLOCKED_BY_FALSIFICATION,
               ROLLBACK_RECOMMENDED)


@dataclass
class BaselineEvidenceIndex:
    """Discoverable evidence paths/refs for one baseline."""

    baseline_id: str
    merge_manifest_path: str = ""
    implementation_intake_path: str = ""
    validation_artifacts: List[str] = field(default_factory=list)
    safety_artifacts: List[str] = field(default_factory=list)
    test_artifacts: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"baseline_id": self.baseline_id,
                "merge_manifest_path": self.merge_manifest_path,
                "implementation_intake_path": self.implementation_intake_path,
                "validation_artifacts": list(self.validation_artifacts),
                "safety_artifacts": list(self.safety_artifacts),
                "test_artifacts": list(self.test_artifacts)}


@dataclass
class BaselineRecord:
    """One registered baseline (append-only; status history preserved)."""

    baseline_id: str
    parent_baseline_id: str = ""
    source_experiment_id: str = ""
    source_branch_spec_id: str = ""
    merge_manifest_path: str = ""
    implementation_intake_path: str = ""
    validation_artifacts: List[str] = field(default_factory=list)
    safety_artifacts: List[str] = field(default_factory=list)
    test_artifacts: List[str] = field(default_factory=list)
    module_changes_summary: List[str] = field(default_factory=list)
    expected_effects: List[str] = field(default_factory=list)
    observed_effects: List[str] = field(default_factory=list)
    known_risks: List[str] = field(default_factory=list)
    unresolved_blockers: List[str] = field(default_factory=list)
    status: str = BaselineStatus.CANDIDATE
    status_history: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    limitations: List[str] = field(default_factory=list)
    created_ts: float = field(default_factory=time.time)

    def set_status(self, status: str, *, reason: str = "") -> None:
        if status not in BaselineStatus.ALL:
            status = BaselineStatus.UNKNOWN
        self.status_history.append({"status": status, "reason": reason,
                                    "ts": time.time()})
        self.status = status

    @property
    def blocked(self) -> bool:
        return self.status in BaselineStatus.BLOCKED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "baseline_id": self.baseline_id,
            "parent_baseline_id": self.parent_baseline_id,
            "source_experiment_id": self.source_experiment_id,
            "source_branch_spec_id": self.source_branch_spec_id,
            "merge_manifest_path": self.merge_manifest_path,
            "implementation_intake_path": self.implementation_intake_path,
            "validation_artifacts": list(self.validation_artifacts),
            "safety_artifacts": list(self.safety_artifacts),
            "test_artifacts": list(self.test_artifacts),
            "module_changes_summary": list(self.module_changes_summary),
            "expected_effects": list(self.expected_effects),
            "observed_effects": list(self.observed_effects),
            "known_risks": list(self.known_risks),
            "unresolved_blockers": list(self.unresolved_blockers),
            "status": self.status,
            "status_history": list(self.status_history),
            "metrics": dict(self.metrics),
            "limitations": list(self.limitations),
            "blocked": self.blocked,
            "created_ts": self.created_ts,
        }


@dataclass
class BaselineRegistry:
    """Append-only registry of baselines + their evidence indexes."""

    state_dir: str = ".solaris_ai_nn_post_merge"
    persist: bool = True
    records: Dict[str, BaselineRecord] = field(default_factory=dict, init=False)
    evidence_index: Dict[str, BaselineEvidenceIndex] = field(
        default_factory=dict, init=False)

    @property
    def _registry_path(self) -> str:
        return os.path.join(self.state_dir, "baseline_registry.json")

    @property
    def _index_path(self) -> str:
        return os.path.join(self.state_dir, "baseline_evidence_index.json")

    def register(self, record: BaselineRecord) -> BaselineRecord:
        if not record.status_history:
            record.set_status(record.status, reason="registered")
        self.records[record.baseline_id] = record
        self.evidence_index[record.baseline_id] = BaselineEvidenceIndex(
            baseline_id=record.baseline_id,
            merge_manifest_path=record.merge_manifest_path,
            implementation_intake_path=record.implementation_intake_path,
            validation_artifacts=list(record.validation_artifacts),
            safety_artifacts=list(record.safety_artifacts),
            test_artifacts=list(record.test_artifacts))
        if self.persist:
            self._write()
        return record

    def get(self, baseline_id: str) -> Optional[BaselineRecord]:
        return self.records.get(baseline_id)

    def update_status(self, baseline_id: str, status: str, *,
                      reason: str = "") -> None:
        rec = self.records.get(baseline_id)
        if rec is not None:
            rec.set_status(status, reason=reason)
            if self.persist:
                self._write()

    def latest_validated(self) -> Optional[BaselineRecord]:
        validated = [r for r in self.records.values()
                     if r.status in (BaselineStatus.VALIDATED,
                                     BaselineStatus.VALIDATED_WITH_WARNINGS)]
        return max(validated, key=lambda r: r.created_ts) if validated else None

    def _write(self) -> None:
        os.makedirs(self.state_dir, exist_ok=True)
        with open(self._registry_path, "w", encoding="utf-8") as fh:
            json.dump({"baseline_count": len(self.records),
                       "baselines": {bid: r.to_dict()
                                     for bid, r in self.records.items()}},
                      fh, indent=2, default=str)
        with open(self._index_path, "w", encoding="utf-8") as fh:
            json.dump({bid: i.to_dict()
                       for bid, i in self.evidence_index.items()},
                      fh, indent=2, default=str)

    def load(self) -> None:
        if os.path.isfile(self._registry_path):
            with open(self._registry_path, encoding="utf-8") as fh:
                data = json.load(fh)
            for bid, payload in data.get("baselines", {}).items():
                payload = dict(payload)
                payload.pop("baseline_id", None)
                payload.pop("blocked", None)
                payload.pop("created_ts", None)
                self.records[bid] = BaselineRecord(baseline_id=bid, **{
                    k: v for k, v in payload.items()
                    if k in BaselineRecord.__dataclass_fields__})

    def status(self) -> Dict[str, Any]:
        statuses = [r.status for r in self.records.values()]
        return {
            "baseline_record_count": len(self.records),
            "baselines": sorted(self.records),
            "candidate_baseline_count": statuses.count(BaselineStatus.CANDIDATE),
            "validated_baseline_count": sum(
                1 for s in statuses
                if s in (BaselineStatus.VALIDATED,
                         BaselineStatus.VALIDATED_WITH_WARNINGS)),
            "blocked_baseline_count": sum(
                1 for s in statuses if s in BaselineStatus.BLOCKED),
            "registry_path": self._registry_path,
            "evidence_index_path": self._index_path,
            "append_only": True,
        }
