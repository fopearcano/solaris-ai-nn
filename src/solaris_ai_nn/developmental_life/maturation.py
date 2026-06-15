"""Maturation -- structural observations over time, NOT consciousness milestones.

The :class:`MaturationDetector` records the first occurrence of structural markers
(first stable proto-concept, first useful prediction, first weakened bad habit, ...)
from the upstream statuses. Markers are *observational* -- they are not
consciousness or developmental-psychology milestones -- and weak/ambiguous markers
are kept separately.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


class MaturationMarkerType:
    FIRST_STABLE_CONCEPT = "first_stable_proto_concept"
    FIRST_STABLE_SIGN = "first_stable_internal_sign"
    FIRST_USEFUL_PREDICTION = "first_useful_prediction"
    FIRST_FAILED_PREDICTION_LEARNING = "first_failed_prediction_learning"
    FIRST_QUESTION_PRESSURE_RESOLUTION = "first_question_pressure_resolution"
    FIRST_USEFUL_INTERNAL_ACTION = "first_useful_internal_action"
    FIRST_HABIT_STRENGTHENED = "first_habit_strengthened"
    FIRST_BAD_HABIT_WEAKENED = "first_bad_habit_weakened"
    FIRST_NO_OP_USEFUL = "first_no_op_useful"
    FIRST_BOUNDARY_RECOVERY = "first_boundary_recovery"
    FIRST_SIMULATION_BOUNDARY_PRESERVED = "first_simulation_boundary_preserved"
    FIRST_SOURCE_UNRELIABILITY_LEARNED = "first_source_unreliability_learned"
    FIRST_CONTAMINATION_REDUCED = "first_human_label_contamination_reduced"
    FIRST_CONSOLIDATION_SUCCESS = "first_consolidation_success"
    FIRST_PLATEAU_RECOVERY = "first_plateau_recovery"

    ALL = (FIRST_STABLE_CONCEPT, FIRST_STABLE_SIGN, FIRST_USEFUL_PREDICTION,
           FIRST_FAILED_PREDICTION_LEARNING,
           FIRST_QUESTION_PRESSURE_RESOLUTION, FIRST_USEFUL_INTERNAL_ACTION,
           FIRST_HABIT_STRENGTHENED, FIRST_BAD_HABIT_WEAKENED,
           FIRST_NO_OP_USEFUL, FIRST_BOUNDARY_RECOVERY,
           FIRST_SIMULATION_BOUNDARY_PRESERVED,
           FIRST_SOURCE_UNRELIABILITY_LEARNED, FIRST_CONTAMINATION_REDUCED,
           FIRST_CONSOLIDATION_SUCCESS, FIRST_PLATEAU_RECOVERY)


@dataclass
class MaturationMarker:
    """One observed structural marker (not a consciousness milestone)."""

    marker_type: str
    tick: int = 0
    marker_id: str = field(default_factory=lambda: f"MAT_{uuid.uuid4().hex[:8]}")
    weak: bool = False
    evidence_refs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"marker_id": self.marker_id, "marker_type": self.marker_type,
                "tick": self.tick, "weak": self.weak,
                "evidence_refs": list(self.evidence_refs),
                "note": "structural observation, NOT a consciousness or "
                        "developmental-psychology milestone"}


@dataclass
class MaturationDetector:
    """Detects first-occurrence structural markers from upstream statuses."""

    markers: List[MaturationMarker] = field(default_factory=list)
    weak_markers: List[MaturationMarker] = field(default_factory=list)
    _seen: set = field(default_factory=set, init=False)

    def _mark(self, mtype: str, tick: int, *, weak: bool = False,
              evidence: List[str] = None) -> None:
        if mtype in self._seen:
            return
        self._seen.add(mtype)
        marker = MaturationMarker(marker_type=mtype, tick=tick, weak=weak,
                                  evidence_refs=list(evidence or []))
        (self.weak_markers if weak else self.markers).append(marker)

    def detect(self, statuses: Dict[str, Dict[str, Any]], *,
               tick: int = 0) -> List[MaturationMarker]:
        ont = statuses.get("perceptual_ontogenesis", {})
        sem = statuses.get("semiogenesis", {})
        cog = statuses.get("sensorium_cognition", {})
        sb = statuses.get("self_boundary", {})
        ar = statuses.get("action_reaction", {})
        M = MaturationMarkerType

        def num(d, k):
            try:
                return float(d.get(k, 0) or 0)
            except (TypeError, ValueError):
                return 0.0

        if num(ont, "stable_concept_count") >= 1:
            self._mark(M.FIRST_STABLE_CONCEPT, tick, evidence=["ontogenesis"])
        if num(sem, "stable_sign_count") >= 1:
            self._mark(M.FIRST_STABLE_SIGN, tick, evidence=["semiogenesis"])
        if num(cog, "prediction_success_rate") > 0.0:
            self._mark(M.FIRST_USEFUL_PREDICTION, tick,
                       weak=num(cog, "prediction_success_rate") < 0.3,
                       evidence=["cognition"])
        if num(cog, "failed_prediction_count") >= 1:
            self._mark(M.FIRST_FAILED_PREDICTION_LEARNING, tick,
                       evidence=["cognition"])
        if num(cog, "question_pressure_resolution_rate") > 0.0:
            self._mark(M.FIRST_QUESTION_PRESSURE_RESOLUTION, tick,
                       evidence=["cognition"])
        if num(ar, "internal_action_count") >= 1 and \
                num(ar, "constructive_reaction_ratio") > 0.0:
            self._mark(M.FIRST_USEFUL_INTERNAL_ACTION, tick,
                       weak=num(ar, "constructive_reaction_ratio") < 0.3,
                       evidence=["action_reaction"])
        if num(ar, "strengthened_habit_count") >= 1:
            self._mark(M.FIRST_HABIT_STRENGTHENED, tick,
                       evidence=["action_reaction"])
        if num(ar, "weakened_habit_count") >= 1:
            self._mark(M.FIRST_BAD_HABIT_WEAKENED, tick,
                       evidence=["action_reaction"])
        if num(ar, "no_op_count") >= 1:
            self._mark(M.FIRST_NO_OP_USEFUL, tick, weak=True,
                       evidence=["action_reaction"])
        if num(sb, "continuity_break_count") >= 1:
            self._mark(M.FIRST_BOUNDARY_RECOVERY, tick, weak=True,
                       evidence=["self_boundary"])
        if num(sb, "simulation_boundary_integrity") >= 1.0:
            self._mark(M.FIRST_SIMULATION_BOUNDARY_PRESERVED, tick,
                       evidence=["self_boundary"])
        return self.markers + self.weak_markers

    def to_dict(self) -> Dict[str, Any]:
        return {
            "maturation_marker_count": len(self.markers),
            "weak_marker_count": len(self.weak_markers),
            "markers": [m.to_dict() for m in self.markers],
            "weak_markers": [m.to_dict() for m in self.weak_markers],
        }
