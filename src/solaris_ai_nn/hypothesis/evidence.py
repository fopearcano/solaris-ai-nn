"""Evidence -- source-scoped, append-only observations about a hypothesis.

Each :class:`EvidenceRecord` keeps the *scope* it came from (offline /
simulated / nursery / latent / real stream). Offline and counterfactual
evidence can never be treated as a real observation, and the ledger is
append-only unless maintenance explicitly archives it.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class EvidenceType:
    SUPPORTING = "supporting"
    WEAKENING = "weakening"
    FALSIFYING = "falsifying"
    INCONCLUSIVE = "inconclusive"
    UNSAFE = "unsafe"
    OFFLINE_SIMULATED = "offline_simulated"
    OBSERVED_REAL_STREAM = "observed_real_stream"
    NURSERY_SIMULATED = "nursery_simulated"
    LATENT_REPLAY = "latent_replay"

    ALL = (SUPPORTING, WEAKENING, FALSIFYING, INCONCLUSIVE, UNSAFE,
           OFFLINE_SIMULATED, OBSERVED_REAL_STREAM, NURSERY_SIMULATED,
           LATENT_REPLAY)
    # Evidence kinds that are NOT real observation of the running system.
    OFFLINE = frozenset({OFFLINE_SIMULATED, LATENT_REPLAY})


# Experiment scope -> whether its evidence counts as offline.
_OFFLINE_SCOPES = frozenset({"latent_replay", "internal_trace_analysis"})


@dataclass
class EvidenceRecord:
    """One source-scoped observation about a hypothesis (append-only)."""

    hypothesis_id: str
    evidence_type: str
    source_scope: str = "internal_trace_analysis"
    observation: str = ""
    metric_deltas: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5
    evidence_refs: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    evidence_id: str = field(
        default_factory=lambda: f"EVD_{uuid.uuid4().hex[:8]}")
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.evidence_type not in EvidenceType.ALL:
            raise ValueError(f"unknown evidence type {self.evidence_type!r}")
        # Offline/counterfactual scopes are never treated as real observation.
        if self.source_scope in _OFFLINE_SCOPES \
                and "offline" not in " ".join(self.limitations).lower():
            self.limitations.append(
                "offline/simulated evidence: not a real observation")

    @property
    def is_offline(self) -> bool:
        return (self.evidence_type in EvidenceType.OFFLINE
                or self.source_scope in _OFFLINE_SCOPES)

    def to_dict(self) -> Dict[str, Any]:
        return {**dict(self.__dict__), "is_offline": self.is_offline}


@dataclass
class EvidenceLedger:
    """Append-only, source-scoped evidence store with JSONL persistence."""

    state_dir: Optional[Union[str, Path]] = None
    write_log: bool = True
    records: List[EvidenceRecord] = field(default_factory=list)
    by_hypothesis: Dict[str, List[str]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.log_path = (Path(self.state_dir) / "hypothesis_evidence.jsonl"
                         if self.state_dir else None)

    def record(self, evidence: EvidenceRecord) -> EvidenceRecord:
        self.records.append(evidence)
        self.by_hypothesis.setdefault(
            evidence.hypothesis_id, []).append(evidence.evidence_id)
        if self.write_log and self.log_path is not None:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(evidence.to_dict(), default=str) + "\n")
        return evidence

    def for_hypothesis(self, hypothesis_id: str) -> List[EvidenceRecord]:
        ids = set(self.by_hypothesis.get(hypothesis_id, []))
        return [r for r in self.records if r.evidence_id in ids]

    def count_by_type(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for record in self.records:
            counts[record.evidence_type] = counts.get(
                record.evidence_type, 0) + 1
        return counts

    def snapshot(self) -> Dict[str, Any]:
        return {
            "evidence_count": len(self.records),
            "by_type": self.count_by_type(),
            "offline_count": sum(1 for r in self.records if r.is_offline),
            "log_path": str(self.log_path) if self.log_path else None,
            "recent": [r.to_dict() for r in self.records[-5:]],
        }


def scope_to_evidence_type(scope: str) -> str:
    """Default evidence type for an experiment scope (before verdict)."""
    return {
        "latent_replay": EvidenceType.LATENT_REPLAY,
        "internal_trace_analysis": EvidenceType.OFFLINE_SIMULATED,
        "nursery_simulation": EvidenceType.NURSERY_SIMULATED,
        "gridworld_simulation": EvidenceType.NURSERY_SIMULATED,
        "read_only_stream_observation": EvidenceType.OBSERVED_REAL_STREAM,
        "sidecar_observation": EvidenceType.OBSERVED_REAL_STREAM,
    }.get(scope, EvidenceType.INCONCLUSIVE)
