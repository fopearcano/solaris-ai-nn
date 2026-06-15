"""Internal action readiness -- conservative gating, never execution.

:class:`ReadinessGate` evaluates whether a desire is ready for its internal action
across multiple dimensions (evidence, energy, attention, memory, boundary clarity,
safety, governance, uncertainty, simulation, consolidation). Readiness is NOT
execution and cannot bypass arbitration; it is deliberately conservative.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class ReadinessState:
    READY = "ready"
    NOT_READY = "not_ready"
    BLOCKED = "blocked"
    DEFER = "defer"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    SAFETY_BLOCKED = "safety_blocked"
    GOVERNANCE_REQUIRED = "governance_required"
    UNKNOWN = "unknown"

    ALL = (READY, NOT_READY, BLOCKED, DEFER, INSUFFICIENT_EVIDENCE,
           SAFETY_BLOCKED, GOVERNANCE_REQUIRED, UNKNOWN)


@dataclass
class ActionReadiness:
    """The readiness assessment for one desire (conservative)."""

    desire_ref: str
    state: str
    dimensions: Dict[str, bool] = field(default_factory=dict)
    reason: str = ""

    @property
    def is_ready(self) -> bool:
        return self.state == ReadinessState.READY

    def to_dict(self) -> Dict[str, Any]:
        return {
            "desire_ref": self.desire_ref,
            "state": self.state,
            "dimensions": dict(self.dimensions),
            "reason": self.reason,
            "note": "readiness is not execution and cannot bypass arbitration",
        }


@dataclass
class ReadinessGate:
    """Evaluates conservative readiness gates for a desire."""

    min_confidence: float = 0.25
    governance_required_kinds: tuple = ("request_operator_review",)

    def evaluate(self, desire: Any, *, energy_ok: bool = True,
                 attention_ok: bool = True, boundary_clear: bool = True,
                 safety_ok: bool = True,
                 governance_ok: bool = True) -> ActionReadiness:
        kind = getattr(desire, "kind", "")
        confidence = float(getattr(desire, "confidence", 0.0))
        uncertainty = float(getattr(desire, "uncertainty", 0.0))
        dims = {
            "evidence_readiness": confidence >= self.min_confidence,
            "energy_budget_readiness": energy_ok,
            "attention_readiness": attention_ok,
            "memory_readiness": True,
            "boundary_clarity_readiness": boundary_clear,
            "safety_readiness": safety_ok,
            "governance_readiness": governance_ok,
            "uncertainty_readiness": uncertainty < 0.8,
            "simulation_readiness": True,
            "consolidation_readiness": True,
        }
        # Safety has veto.
        if not safety_ok:
            return ActionReadiness(getattr(desire, "desire_id", ""),
                                   ReadinessState.SAFETY_BLOCKED, dims,
                                   "safety gate not satisfied")
        # Governance-required kinds need governance readiness.
        if kind in self.governance_required_kinds and not governance_ok:
            return ActionReadiness(getattr(desire, "desire_id", ""),
                                   ReadinessState.GOVERNANCE_REQUIRED, dims,
                                   "governance review required")
        if not dims["evidence_readiness"]:
            return ActionReadiness(getattr(desire, "desire_id", ""),
                                   ReadinessState.INSUFFICIENT_EVIDENCE, dims,
                                   "confidence below threshold")
        if not boundary_clear:
            return ActionReadiness(getattr(desire, "desire_id", ""),
                                   ReadinessState.DEFER, dims,
                                   "boundary clarity insufficient")
        if not (energy_ok and attention_ok and dims["uncertainty_readiness"]):
            return ActionReadiness(getattr(desire, "desire_id", ""),
                                   ReadinessState.NOT_READY, dims,
                                   "energy/attention/uncertainty gate")
        return ActionReadiness(getattr(desire, "desire_id", ""),
                               ReadinessState.READY, dims, "all gates passed")
