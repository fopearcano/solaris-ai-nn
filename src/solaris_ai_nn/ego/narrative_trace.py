"""Narrative trace -- a compact continuity story from grounded events.

Deterministic templates only: every narrative event is built from a fixed
template plus recorded values, must reference evidence, and avoids
first-person statements by default ("The system entered embodied simulation
mode", never "I woke up"). The trace persists as JSONL so the continuity
story of a run survives the run.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# template_id -> deterministic sentence template.
TEMPLATES: Dict[str, str] = {
    "run_started": "Run started (run_id={run_id}).",
    "run_started_from_checkpoint":
        "Run started from checkpoint {checkpoint}.",
    "perspective_shift":
        "The system entered {mode} mode because {reason}.",
    "sidecar_signal": "A sidecar signal was observed ({detail}).",
    "sidecar_attached": "A Solaris_Ai sidecar was attached (observe-only).",
    "sidecar_detached": "The Solaris_Ai sidecar was detached.",
    "desire_inhibited":
        "A desire candidate ({label}) was inhibited by {family}.",
    "counterfactual_generated":
        "A counterfactual replay was generated offline ({detail}).",
    "replay_generated":
        "An offline replay was generated ({detail}).",
    "emergency_stop": "Emergency stop was requested ({reason}).",
    "identity_uncertain":
        "Identity continuity is uncertain because {reason}.",
    "boundary_crossed":
        "The {boundary} was crossed safely ({description}).",
    "boundary_violated":
        "The {boundary} was violated ({description}).",
    "checkpoint_saved": "A checkpoint was saved at step {step}.",
    "operator_instruction":
        "An operator instruction was received via the operator interface "
        "({detail}).",
    "stream_observed":
        "A read-only stream event was observed ({detail}).",
    "action_suggested":
        "The executive suggested {label} (a suggestion, not a committed "
        "action).",
    "self_report_generated": "A self-report was generated at {path}.",
}

# Words that would smuggle personhood into the narrative.
_FORBIDDEN_FRAGMENTS = ("i am", "i want", "i feel", "i know myself",
                        "my soul", "i chose", "i woke")


@dataclass
class NarrativeTraceEvent:
    """One templated, evidence-backed narrative sentence."""

    template_id: str
    text: str
    evidence_refs: List[str]
    step: int = 0
    category: str = "runtime"
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class NarrativeTrace:
    """Bounded, persistable sequence of narrative events."""

    state_dir: Optional[Union[str, Path]] = None
    max_events: int = 500
    events: List[NarrativeTraceEvent] = field(default_factory=list,
                                              init=False)
    rows_written: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self.trace_path = (Path(self.state_dir) / "narrative_trace.jsonl"
                           if self.state_dir else None)

    def add(self, template_id: str, evidence: List[str], step: int = 0,
            category: str = "runtime", **values: Any) -> NarrativeTraceEvent:
        """Render a template into a narrative event. Evidence is mandatory."""
        if template_id not in TEMPLATES:
            raise ValueError(f"unknown narrative template {template_id!r}")
        if not evidence:
            raise ValueError("every narrative event must reference "
                             "evidence")
        fmt = {k: str(v) for k, v in values.items()}
        fmt.setdefault("step", str(step))
        text = TEMPLATES[template_id].format(**fmt)
        lowered = text.lower()
        for fragment in _FORBIDDEN_FRAGMENTS:
            if fragment in lowered:
                raise ValueError(
                    f"narrative text contains forbidden first-person "
                    f"fragment {fragment!r}")
        event = NarrativeTraceEvent(template_id=template_id, text=text,
                                    evidence_refs=list(evidence),
                                    step=step, category=category)
        self.events.append(event)
        self.events = self.events[-self.max_events:]
        self._write(event)
        return event

    def _write(self, event: NarrativeTraceEvent) -> None:
        if self.trace_path is None:
            return
        self.trace_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.trace_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(event.to_dict(), default=str) + "\n")
        self.rows_written += 1

    # -- views --------------------------------------------------------------------

    def tail(self, limit: int = 10) -> List[NarrativeTraceEvent]:
        return self.events[-limit:]

    def as_story(self, limit: int = 20) -> str:
        return "\n".join(e.text for e in self.events[-limit:])

    def snapshot(self) -> Dict[str, Any]:
        return {
            "events_in_memory": len(self.events),
            "rows_written": self.rows_written,
            "trace_path": str(self.trace_path) if self.trace_path else None,
            "recent": [e.to_dict() for e in self.events[-5:]],
            "note": ("deterministic templates over recorded events; no "
                     "first-person or personhood claims"),
        }
