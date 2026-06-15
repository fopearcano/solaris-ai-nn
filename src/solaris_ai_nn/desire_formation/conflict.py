"""Desire conflict -- competing internal tendencies, fed to LOGOS, never hidden.

The :class:`ConflictDetector` surfaces conflicts between desire candidates
(novelty-vs-stability, inspect-vs-consolidate, safety-vs-desire, ...). Conflicts
feed LOGOS, may inhibit or defer desires, and must not be hidden.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .desire import DesireKind


class ConflictType:
    NOVELTY_VS_STABILITY = "novelty_vs_stability"
    INSPECT_VS_CONSOLIDATE = "inspect_vs_consolidate"
    FOCUS_VS_RECOVER_NEGLECTED = "focus_one_modality_vs_recover_neglected"
    RESOLVE_VS_PRESERVE = "resolve_tension_vs_preserve_unknown"
    SIMULATE_VS_OBSERVE = "simulate_vs_observe"
    ACT_NOW_VS_WAIT = "act_now_vs_wait"
    SOURCE_TRUST_VS_NEED = "source_trust_vs_source_need"
    HUMAN_LABEL_VS_FEATURE = "human_label_vs_feature_evidence"
    SAFETY_VS_DESIRE = "safety_vs_desire"
    GOVERNANCE_VS_DESIRE = "governance_vs_desire"
    UNKNOWN = "unknown_conflict"

    ALL = (NOVELTY_VS_STABILITY, INSPECT_VS_CONSOLIDATE,
           FOCUS_VS_RECOVER_NEGLECTED, RESOLVE_VS_PRESERVE, SIMULATE_VS_OBSERVE,
           ACT_NOW_VS_WAIT, SOURCE_TRUST_VS_NEED, HUMAN_LABEL_VS_FEATURE,
           SAFETY_VS_DESIRE, GOVERNANCE_VS_DESIRE, UNKNOWN)


# Pairs of desire kinds that conflict.
_CONFLICT_PAIRS = {
    frozenset({DesireKind.FOCUS_MODALITY, DesireKind.STABILIZE_CONCEPT}):
        ConflictType.NOVELTY_VS_STABILITY,
    frozenset({DesireKind.INSPECT_ABSENCE, DesireKind.CONSOLIDATE_MEMORY}):
        ConflictType.INSPECT_VS_CONSOLIDATE,
    frozenset({DesireKind.FOCUS_MODALITY,
               DesireKind.RECOVER_NEGLECTED_MODALITY}):
        ConflictType.FOCUS_VS_RECOVER_NEGLECTED,
    frozenset({DesireKind.RESOLVE_LOGOS_TENSION, DesireKind.PRESERVE_UNKNOWN}):
        ConflictType.RESOLVE_VS_PRESERVE,
    frozenset({DesireKind.RUN_INTERNAL_SIMULATION, DesireKind.TEST_PREDICTION}):
        ConflictType.SIMULATE_VS_OBSERVE,
}


@dataclass
class DesireConflict:
    """One conflict between desires (fed to LOGOS; never hidden)."""

    conflict_type: str
    desire_refs: List[str] = field(default_factory=list)
    conflict_id: str = field(default_factory=lambda: f"CFL_{uuid.uuid4().hex[:8]}")
    intensity: float = 0.0
    detail: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"conflict_id": self.conflict_id,
                "conflict_type": self.conflict_type,
                "desire_refs": list(self.desire_refs),
                "intensity": round(self.intensity, 4),
                "detail": self.detail,
                "note": "desire conflict feeds LOGOS; not hidden"}


@dataclass
class ConflictDetector:
    """Detects conflicts among desire candidates."""

    conflicts: List[DesireConflict] = field(default_factory=list)

    def detect(self, desires: List[Any]) -> List[DesireConflict]:
        self.conflicts = []
        kinds = {getattr(d, "kind", ""): getattr(d, "desire_id", "")
                 for d in desires}
        for pair, ctype in _CONFLICT_PAIRS.items():
            present = [k for k in pair if k in kinds]
            if len(present) == len(pair):
                self.conflicts.append(DesireConflict(
                    conflict_type=ctype,
                    desire_refs=[kinds[k] for k in present],
                    intensity=0.5, detail=f"{' / '.join(present)}"))
        return self.conflicts

    def add_safety_conflict(self, desire_ref: str) -> DesireConflict:
        c = DesireConflict(conflict_type=ConflictType.SAFETY_VS_DESIRE,
                           desire_refs=[desire_ref], intensity=1.0,
                           detail="safety vetoed a desire")
        self.conflicts.append(c)
        return c

    def add_governance_conflict(self, desire_ref: str) -> DesireConflict:
        c = DesireConflict(conflict_type=ConflictType.GOVERNANCE_VS_DESIRE,
                           desire_refs=[desire_ref], intensity=0.8,
                           detail="governance review required")
        self.conflicts.append(c)
        return c

    def to_dict(self) -> Dict[str, Any]:
        return {"conflict_count": len(self.conflicts),
                "conflicts": [c.to_dict() for c in self.conflicts]}
