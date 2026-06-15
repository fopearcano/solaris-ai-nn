"""Attention economy -- a finite, explainable allocation of internal attention.

An :class:`AttentionEconomy` distributes a finite attention budget across targets
(modalities, receptors, sources, absence windows, rhythm/invariant/cross-modal
candidates, hypothesis gaps, LOGOS tensions, memory traces, proto-symbol
candidates). Every :class:`AttentionAllocation` carries an explanation, a slice is
always reserved to recover neglected modalities, and attention shifts only
internal polling/processing priority -- it never starts a sensor or modifies a
source.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class AttentionTarget:
    MODALITY = "modality"
    RECEPTOR = "receptor"
    SOURCE = "source_id"
    ABSENCE_WINDOW = "absence_window"
    RHYTHM_CANDIDATE = "rhythm_candidate"
    INVARIANT_CANDIDATE = "invariant_candidate"
    CROSS_MODAL_RELATION = "cross_modal_relation"
    HYPOTHESIS_GAP = "hypothesis_gap"
    LOGOS_TENSION = "logos_tension"
    MEMORY_TRACE = "memory_trace"
    PROTO_SYMBOL_CANDIDATE = "proto_symbol_candidate"
    NEGLECTED_MODALITY_RECOVERY = "neglected_modality_recovery"

    ALL = (MODALITY, RECEPTOR, SOURCE, ABSENCE_WINDOW, RHYTHM_CANDIDATE,
           INVARIANT_CANDIDATE, CROSS_MODAL_RELATION, HYPOTHESIS_GAP,
           LOGOS_TENSION, MEMORY_TRACE, PROTO_SYMBOL_CANDIDATE,
           NEGLECTED_MODALITY_RECOVERY)


@dataclass
class AttentionAllocation:
    target_type: str
    target: str
    weight: float
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class AttentionMarketState:
    total_budget: float
    allocations: List[AttentionAllocation] = field(default_factory=list)
    reallocation_count: int = 0
    neglected_recovery_reserved: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_budget": self.total_budget,
            "allocations": [a.to_dict() for a in self.allocations],
            "reallocation_count": self.reallocation_count,
            "neglected_recovery_reserved": self.neglected_recovery_reserved,
            "allocation_count": len(self.allocations),
            "note": "internal polling/processing priority only; no sensor "
                    "control",
        }


@dataclass
class AttentionEconomy:
    """Allocates a finite, explainable attention budget across targets."""

    total_budget: float = 1.0
    neglected_recovery_fraction: float = 0.1
    state: AttentionMarketState = field(default=None, init=False)

    def allocate(self, field_state: Any, receptors: List[Any], needs: Any,
                 ) -> AttentionMarketState:
        # Reserve a slice for recovering neglected modalities.
        reserved = self.total_budget * self.neglected_recovery_fraction
        spendable = self.total_budget - reserved
        demands: List[AttentionAllocation] = []

        def demand(target_type: str, target: str, raw: float,
                   reason: str) -> None:
            demands.append(AttentionAllocation(
                target_type=target_type, target=target,
                weight=max(0.0, raw), reason=reason))

        # Field pressures create demand.
        demand(AttentionTarget.MODALITY,
               getattr(field_state, "dominant_modality", "?") or "?",
               getattr(field_state, "novelty_pressure", 0.0),
               "novelty pressure on the dominant modality")
        demand(AttentionTarget.ABSENCE_WINDOW, "absence",
               getattr(field_state, "absence_pressure", 0.0),
               "absence pressure")
        demand(AttentionTarget.RHYTHM_CANDIDATE, "rhythm",
               getattr(field_state, "rhythm_pressure", 0.0),
               "rhythm pressure")
        demand(AttentionTarget.CROSS_MODAL_RELATION, "cross_modal",
               getattr(field_state, "cross_modal_pressure", 0.0),
               "cross-modal pressure")
        # Needs create demand.
        for need in getattr(needs, "needs", {}).values():
            if need.pressure >= need.saturation_threshold:
                demand(AttentionTarget.HYPOTHESIS_GAP, need.need_type,
                       need.pressure, f"{need.need_type} is saturated")
        # Fatigued receptors demand recovery attention.
        for r in receptors:
            if getattr(r, "fatigue", 0.0) >= 0.6:
                demand(AttentionTarget.RECEPTOR, getattr(r, "receptor_id", "?"),
                       getattr(r, "fatigue", 0.0), "receptor fatigue")

        total_raw = sum(d.weight for d in demands) or 1.0
        allocations: List[AttentionAllocation] = []
        for d in demands:
            allocations.append(AttentionAllocation(
                target_type=d.target_type, target=d.target,
                weight=round(spendable * d.weight / total_raw, 4),
                reason=d.reason))
        # The reserved recovery slice is always present.
        allocations.append(AttentionAllocation(
            AttentionTarget.NEGLECTED_MODALITY_RECOVERY, "neglected",
            round(reserved, 4),
            "reserved so neglected modalities are periodically revisited"))

        prev = self.state.allocations if self.state else []
        reallocs = (self.state.reallocation_count if self.state else 0)
        if prev and {a.target for a in prev} != {a.target for a in allocations}:
            reallocs += 1
        self.state = AttentionMarketState(
            total_budget=self.total_budget, allocations=allocations,
            reallocation_count=reallocs,
            neglected_recovery_reserved=round(reserved, 4))
        return self.state
