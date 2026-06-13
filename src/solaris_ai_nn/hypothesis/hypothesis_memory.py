"""Hypothesis memory -- the record of what was wondered and what was learned.

Tracks proposed / tested / supported / falsified / inconclusive /
unsafe-to-test hypotheses, repeated hypothesis families, long-lived unknowns,
and hypotheses that became world-model edges or proto-symbol rules. Persists
to JSON (current set) and JSONL (append-only history). Bounded in memory.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .hypotheses import Hypothesis, HypothesisStatus


@dataclass
class HypothesisHistoryRecord:
    """One append-only entry in the hypothesis history."""

    hypothesis_id: str
    event: str  # proposed | scheduled | tested | status_change | promoted
    status: str = ""
    detail: str = ""
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


# A hypothesis untested for this many proposals is a "long-lived unknown".
LONG_LIVED_THRESHOLD = 20


@dataclass
class HypothesisMemory:
    """Bounded, persisted memory of hypotheses and their fates."""

    state_dir: Optional[Union[str, Path]] = None
    write_log: bool = True
    max_hypotheses: int = 2000
    hypotheses: Dict[str, Hypothesis] = field(default_factory=dict)
    history: List[HypothesisHistoryRecord] = field(default_factory=list)
    promoted_to_world_model: List[str] = field(default_factory=list)
    promoted_to_proto_symbol: List[str] = field(default_factory=list)
    _proposal_counter: int = field(default=0, init=False)
    _proposed_at: Dict[str, int] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self.hyp_path = (Path(self.state_dir) / "hypotheses.json"
                         if self.state_dir else None)
        self.history_path = (
            Path(self.state_dir) / "hypothesis_history.jsonl"
            if self.state_dir else None)

    # -- recording ----------------------------------------------------------------

    def add(self, hypothesis: Hypothesis) -> Hypothesis:
        if hypothesis.hypothesis_id not in self.hypotheses:
            self._proposal_counter += 1
            self._proposed_at[hypothesis.hypothesis_id] = \
                self._proposal_counter
            self._log(hypothesis.hypothesis_id, "proposed",
                      hypothesis.status, hypothesis.statement[:80])
        self.hypotheses[hypothesis.hypothesis_id] = hypothesis
        if len(self.hypotheses) > self.max_hypotheses:
            # Drop the oldest closed hypotheses first.
            closed = [h for h in self.hypotheses.values()
                      if h.status in HypothesisStatus.CLOSED]
            for h in closed[:len(self.hypotheses) - self.max_hypotheses]:
                self.hypotheses.pop(h.hypothesis_id, None)
        return hypothesis

    def record_status(self, hypothesis: Hypothesis, detail: str = "") -> None:
        self.hypotheses[hypothesis.hypothesis_id] = hypothesis
        self._log(hypothesis.hypothesis_id, "status_change",
                  hypothesis.status, detail)

    def record_promotion(self, hypothesis_id: str, target: str) -> None:
        if target == "world_model":
            self.promoted_to_world_model.append(hypothesis_id)
        elif target == "proto_symbol":
            self.promoted_to_proto_symbol.append(hypothesis_id)
        self._log(hypothesis_id, "promoted", "", f"to {target}")

    def _log(self, hypothesis_id: str, event: str, status: str,
             detail: str) -> None:
        record = HypothesisHistoryRecord(
            hypothesis_id=hypothesis_id, event=event, status=status,
            detail=detail)
        self.history.append(record)
        self.history = self.history[-5000:]
        if self.write_log and self.history_path is not None:
            self.history_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(record.to_dict(), default=str) + "\n")

    # -- views --------------------------------------------------------------------

    def by_status(self, status: str) -> List[Hypothesis]:
        return [h for h in self.hypotheses.values() if h.status == status]

    def counts_by_status(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for h in self.hypotheses.values():
            counts[h.status] = counts.get(h.status, 0) + 1
        return counts

    def family_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for h in self.hypotheses.values():
            counts[h.type] = counts.get(h.type, 0) + 1
        return counts

    def long_lived_unknowns(self) -> List[Hypothesis]:
        """Proposed-but-never-resolved hypotheses that have aged out."""
        out = []
        for h in self.hypotheses.values():
            if h.status in (HypothesisStatus.PROPOSED,
                            HypothesisStatus.INCONCLUSIVE):
                age = self._proposal_counter - self._proposed_at.get(
                    h.hypothesis_id, self._proposal_counter)
                if age >= LONG_LIVED_THRESHOLD:
                    out.append(h)
        return out

    def save_state(self) -> None:
        if self.hyp_path is None:
            return
        self.hyp_path.parent.mkdir(parents=True, exist_ok=True)
        self.hyp_path.write_text(json.dumps({
            "hypotheses": {hid: h.to_dict()
                           for hid, h in self.hypotheses.items()},
            "promoted_to_world_model": self.promoted_to_world_model,
            "promoted_to_proto_symbol": self.promoted_to_proto_symbol,
        }, indent=2, default=str), encoding="utf-8")

    def snapshot(self) -> Dict[str, Any]:
        return {
            "hypothesis_count": len(self.hypotheses),
            "counts_by_status": self.counts_by_status(),
            "family_counts": self.family_counts(),
            "long_lived_unknown_count": len(self.long_lived_unknowns()),
            "promoted_to_world_model": len(self.promoted_to_world_model),
            "promoted_to_proto_symbol": len(self.promoted_to_proto_symbol),
            "history_length": len(self.history),
        }
