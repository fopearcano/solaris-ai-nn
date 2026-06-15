"""Anticipation -- operational expectation over signs/absences/rhythms.

:class:`AnticipationEngine` tracks operational expectations (expected signs,
absences, rhythms, source changes, field pressure, LOGOS tensions, attention
shifts). Anticipation is operational expectation, NOT imagination or subjective
experience, and it feeds changed-perception probes.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


class AnticipationKind:
    EXPECTED_SIGN = "expected_sign"
    EXPECTED_ABSENCE = "expected_absence"
    EXPECTED_RHYTHM = "expected_rhythm"
    EXPECTED_SOURCE_CHANGE = "expected_source_change"
    EXPECTED_FIELD_PRESSURE = "expected_field_pressure"
    EXPECTED_LOGOS_TENSION = "expected_logos_tension"
    EXPECTED_ATTENTION_SHIFT = "expected_attention_shift"

    ALL = (EXPECTED_SIGN, EXPECTED_ABSENCE, EXPECTED_RHYTHM,
           EXPECTED_SOURCE_CHANGE, EXPECTED_FIELD_PRESSURE,
           EXPECTED_LOGOS_TENSION, EXPECTED_ATTENTION_SHIFT)


@dataclass
class AnticipationEvent:
    """One operational expectation (not imagination, not subjective experience)."""

    kind: str
    target: str
    event_id: str = field(default_factory=lambda: f"ANT_{uuid.uuid4().hex[:8]}")
    confidence: float = 0.0
    evidence_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "kind": self.kind,
            "target": self.target,
            "confidence": round(self.confidence, 4),
            "evidence_refs": list(self.evidence_refs),
            "note": "operational expectation; not imagination or subjective "
                    "experience",
        }


@dataclass
class AnticipationState:
    events: List[AnticipationEvent] = field(default_factory=list)

    def expected_targets(self) -> List[str]:
        return [e.target for e in self.events]

    def to_dict(self) -> Dict[str, Any]:
        by_kind: Dict[str, int] = {}
        for e in self.events:
            by_kind[e.kind] = by_kind.get(e.kind, 0) + 1
        return {"event_count": len(self.events), "by_kind": by_kind,
                "events": [e.to_dict() for e in self.events],
                "probe_targets": self.expected_targets(),
                "note": "anticipation feeds changed-perception probes"}


@dataclass
class AnticipationEngine:
    """Builds operational expectations from predictions (feeds probes)."""

    state: AnticipationState = field(default_factory=AnticipationState)

    def update(self, predictions: List[Any]) -> AnticipationState:
        self.state = AnticipationState()
        for p in predictions:
            ptype = getattr(p, "prediction_type", "")
            if ptype == "next_sign":
                kind = AnticipationKind.EXPECTED_SIGN
            elif ptype in ("missing_sign", "source_silence"):
                kind = AnticipationKind.EXPECTED_ABSENCE
            elif ptype == "cross_modal_relation":
                kind = AnticipationKind.EXPECTED_SOURCE_CHANGE
            elif ptype == "logos_tension":
                kind = AnticipationKind.EXPECTED_LOGOS_TENSION
            elif ptype == "attention_need":
                kind = AnticipationKind.EXPECTED_ATTENTION_SHIFT
            else:
                kind = AnticipationKind.EXPECTED_FIELD_PRESSURE
            self.state.events.append(AnticipationEvent(
                kind=kind, target=getattr(p, "predicted_target", ""),
                confidence=float(getattr(p, "confidence", 0.0)),
                evidence_refs=[getattr(p, "prediction_id", "")]))
        return self.state

    def probe_payload(self) -> Dict[str, Any]:
        """A bounded payload a changed-perception probe could consume."""
        return {"expected_targets": self.state.expected_targets(),
                "event_count": len(self.state.events),
                "note": "expectations only; probe is read-only and internal"}
