"""Life history -- operational trace history, NOT biography or personhood.

The :class:`LifeHistoryBuilder` summarizes major operational events over the run
(sensory shifts, concept/sign births, prediction failures, action-effect
discoveries, habit formation, boundary breaks, contamination episodes, phase
transitions, regressions, plateaus). This is operational history, never a biography;
every event carries evidence refs and nothing is anthropomorphized.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


class LifeHistoryEventKind:
    SENSORY_SHIFT = "major_sensory_shift"
    CONCEPT_BIRTH = "major_concept_birth"
    SIGN_BIRTH = "major_sign_birth"
    PREDICTION_FAILURE = "major_prediction_failure"
    ACTION_EFFECT_DISCOVERY = "major_action_effect_discovery"
    HABIT_FORMATION = "habit_formation"
    INHIBITION_LEARNING = "inhibition_learning"
    BOUNDARY_BREAK = "boundary_break"
    CONTINUITY_RECOVERY = "continuity_recovery"
    SOURCE_DIET_SHIFT = "source_diet_shift"
    CONTAMINATION_EVENT = "contamination_event"
    OVERLOAD_DEPRIVATION = "overload_deprivation_episode"
    CONSOLIDATION = "consolidation_episode"
    PHASE_TRANSITION = "phase_transition"
    REGRESSION = "regression"
    PLATEAU = "plateau"

    ALL = (SENSORY_SHIFT, CONCEPT_BIRTH, SIGN_BIRTH, PREDICTION_FAILURE,
           ACTION_EFFECT_DISCOVERY, HABIT_FORMATION, INHIBITION_LEARNING,
           BOUNDARY_BREAK, CONTINUITY_RECOVERY, SOURCE_DIET_SHIFT,
           CONTAMINATION_EVENT, OVERLOAD_DEPRIVATION, CONSOLIDATION,
           PHASE_TRANSITION, REGRESSION, PLATEAU)


@dataclass
class LifeHistoryEvent:
    """One operational life-history event (not biography; evidence required)."""

    kind: str
    tick: int = 0
    event_id: str = field(default_factory=lambda: f"LHE_{uuid.uuid4().hex[:8]}")
    detail: str = ""
    evidence_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"event_id": self.event_id, "kind": self.kind, "tick": self.tick,
                "detail": self.detail, "evidence_refs": list(self.evidence_refs),
                "note": "operational trace event, not biography"}


@dataclass
class OperationalLifeHistory:
    events: List[LifeHistoryEvent] = field(default_factory=list)

    def distribution(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for e in self.events:
            out[e.kind] = out.get(e.kind, 0) + 1
        return out

    def to_dict(self) -> Dict[str, Any]:
        return {"event_count": len(self.events),
                "distribution": self.distribution(),
                "events": [e.to_dict() for e in self.events],
                "note": "operational history, not biography or personhood"}


@dataclass
class LifeHistoryBuilder:
    """Builds operational life-history events from per-tick statuses/markers."""

    history: OperationalLifeHistory = field(
        default_factory=OperationalLifeHistory)

    def record(self, kind: str, tick: int, *, detail: str = "",
               evidence_refs: List[str] = None) -> LifeHistoryEvent:
        if kind not in LifeHistoryEventKind.ALL:
            return LifeHistoryEvent(kind=LifeHistoryEventKind.SENSORY_SHIFT,
                                    tick=tick)
        ev = LifeHistoryEvent(kind=kind, tick=tick, detail=detail,
                              evidence_refs=list(evidence_refs or []))
        self.history.events.append(ev)
        return ev

    def build_from_tick(self, statuses: Dict[str, Dict[str, Any]], *,
                        maturation_markers: List[Any] = None,
                        regressions: List[Any] = None,
                        plateaus: List[Any] = None, tick: int = 0) -> None:
        K = LifeHistoryEventKind
        met = statuses.get("perceptual_metabolism", {})
        if met.get("overload_state") or met.get("deprivation_state"):
            self.record(K.OVERLOAD_DEPRIVATION, tick,
                        detail="metabolic episode", evidence_refs=["metabolism"])
        for m in (maturation_markers or []):
            mtype = getattr(m, "marker_type", "")
            if "concept" in mtype:
                self.record(K.CONCEPT_BIRTH, tick, detail=mtype,
                            evidence_refs=[getattr(m, "marker_id", "")])
            elif "sign" in mtype:
                self.record(K.SIGN_BIRTH, tick, detail=mtype,
                            evidence_refs=[getattr(m, "marker_id", "")])
            elif "habit" in mtype:
                self.record(K.HABIT_FORMATION, tick, detail=mtype,
                            evidence_refs=[getattr(m, "marker_id", "")])
        for r in (regressions or []):
            self.record(K.REGRESSION, tick, detail=getattr(r, "reason", ""),
                        evidence_refs=[getattr(r, "regression_id", "")])
        for p in (plateaus or []):
            self.record(K.PLATEAU, tick, detail=getattr(p, "reason", ""),
                        evidence_refs=[getattr(p, "plateau_id", "")])
