"""Decision traces -- every arbitration, fully written down.

Each decision records the input desires, the generated candidates, what was
inhibited and why, the prospection estimates, the full score table, the
selection, the rejected field, and the final reason. Rows append to
``decision_trace.jsonl``; the latest executive state and plan persist as
JSON.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


@dataclass
class DecisionTraceEvent:
    """One recorded arbitration."""

    step: int = 0
    mode: str = "arbitrated"
    input_desires: List[str] = field(default_factory=list)
    candidates: List[str] = field(default_factory=list)
    inhibited: List[Dict[str, str]] = field(default_factory=list)
    prospection: Dict[str, Any] = field(default_factory=dict)
    scores: List[Dict[str, Any]] = field(default_factory=list)
    selected: Optional[str] = None
    rejected: List[str] = field(default_factory=list)
    reason: str = ""
    fallback_used: bool = False
    safety_status: str = "ok"
    governance_status: str = "ok"
    context_summary: Dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class DecisionTrace:
    """A bounded in-memory window over the recorded events."""

    capacity: int = 100
    events: List[DecisionTraceEvent] = field(default_factory=list)

    def add(self, event: DecisionTraceEvent) -> DecisionTraceEvent:
        self.events.append(event)
        self.events = self.events[-self.capacity:]
        return event

    def last(self) -> Optional[DecisionTraceEvent]:
        return self.events[-1] if self.events else None

    def __len__(self) -> int:
        return len(self.events)


@dataclass
class DecisionTraceRecorder:
    """Records decisions in memory and (optionally) on disk."""

    state_dir: Optional[Union[str, Path]] = None
    trace: DecisionTrace = field(default_factory=DecisionTrace)
    rows_written: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if self.state_dir is not None:
            self.state_dir = Path(self.state_dir)
            self.trace_path = self.state_dir / "decision_trace.jsonl"
            self.state_path = self.state_dir / "executive_state.json"
            self.plan_path = self.state_dir / "current_plan.json"
        else:
            self.trace_path = self.state_path = self.plan_path = None

    def record(self, event: DecisionTraceEvent) -> DecisionTraceEvent:
        self.trace.add(event)
        if self.trace_path is not None:
            self.trace_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.trace_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(event.to_dict(), default=str) + "\n")
            self.rows_written += 1
        return event

    def record_decision(self, step: int, mode: str, queue: Any,
                        candidates: Any, result: Any,
                        prospection: Optional[Dict[str, Any]] = None,
                        context_summary: Optional[Dict[str, Any]] = None,
                        ) -> DecisionTraceEvent:
        """Assemble and record one full arbitration."""
        all_candidates = list(getattr(candidates, "candidates", candidates))
        inhibited = [{"label": c.label, "reason": c.inhibition_reason}
                     for c in all_candidates if c.inhibited]
        inhibited += [{"label": i.proposal, "reason": i.inhibition_reason}
                      for i in getattr(queue, "items", [])
                      if i.inhibited]
        selected_label = (result.selected.label
                          if result.selected is not None else None)
        event = DecisionTraceEvent(
            step=step, mode=mode,
            input_desires=[i.proposal
                           for i in getattr(queue, "items", [])][:15],
            candidates=[c.label for c in all_candidates][:15],
            inhibited=inhibited[:15],
            prospection=prospection or {},
            scores=[s.to_dict() for s in result.scores][:15],
            selected=selected_label,
            rejected=[s.candidate.label for s in result.scores
                      if s.candidate.label != selected_label][:15],
            reason=result.reason,
            fallback_used=result.fallback_used,
            context_summary=context_summary or {})
        return self.record(event)

    def save_state(self, snapshot: Dict[str, Any],
                   plan: Optional[Dict[str, Any]] = None) -> None:
        if self.state_path is None:
            return
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_path, "w", encoding="utf-8") as fh:
            json.dump(snapshot, fh, indent=2, default=str)
        if plan is not None:
            with open(self.plan_path, "w", encoding="utf-8") as fh:
                json.dump(plan, fh, indent=2, default=str)

    def rows(self) -> List[Dict[str, Any]]:
        if self.trace_path is None or not self.trace_path.exists():
            return [e.to_dict() for e in self.trace.events]
        out = []
        with open(self.trace_path, "r", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    out.append(json.loads(line))
        return out

    def snapshot(self) -> Dict[str, Any]:
        last = self.trace.last()
        return {
            "events_in_memory": len(self.trace),
            "rows_written": self.rows_written,
            "trace_path": (str(self.trace_path)
                           if self.trace_path else None),
            "last_decision": last.to_dict() if last else None,
        }
