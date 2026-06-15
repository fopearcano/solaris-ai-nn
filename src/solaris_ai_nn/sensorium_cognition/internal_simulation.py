"""Internal simulation -- bounded, internal-only, always marked non-real.

An :class:`InternalSimulation` runs a bounded internal "what if" over signs/
relations/absences/etc. Simulation is internal only, creates no external evidence,
is always marked simulated/counterfactual, is never treated as a live observation,
and is strictly bounded.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List


class SimulationScope:
    SIGN_SEQUENCE = "sign_sequence"
    ABSENCE_WINDOW = "absence_window"
    CROSS_MODAL_RELATION = "cross_modal_relation"
    SOURCE_HEALTH = "source_health"
    ATTENTION_SHIFT = "attention_shift"
    METABOLIC_STATE = "metabolic_state"
    LOGOS_TENSION = "LOGOS_tension"
    WORLD_MODEL_RELATION = "world_model_relation"

    ALL = (SIGN_SEQUENCE, ABSENCE_WINDOW, CROSS_MODAL_RELATION, SOURCE_HEALTH,
           ATTENTION_SHIFT, METABOLIC_STATE, LOGOS_TENSION,
           WORLD_MODEL_RELATION)


@dataclass
class SimulationStep:
    """One step of an internal simulation (always simulated, never observed)."""

    index: int
    sign_ref: str
    note: str = ""
    simulated: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {"index": self.index, "sign_ref": self.sign_ref,
                "note": self.note, "simulated": True}


@dataclass
class SimulationResult:
    """The bounded result of one internal simulation (marked non-real)."""

    scope: str
    steps: List[SimulationStep] = field(default_factory=list)
    simulation_id: str = field(
        default_factory=lambda: f"SIM_{uuid.uuid4().hex[:8]}")
    usefulness: float = 0.0
    seeds_hypothesis: bool = False
    evidence_refs: List[str] = field(default_factory=list)
    is_real_observation: bool = False  # always False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "simulation_id": self.simulation_id,
            "scope": self.scope,
            "step_count": len(self.steps),
            "steps": [s.to_dict() for s in self.steps],
            "usefulness": round(self.usefulness, 4),
            "seeds_hypothesis": self.seeds_hypothesis,
            "evidence_refs": list(self.evidence_refs),
            "is_real_observation": False,
            "simulated": True,
            "note": "internal simulation only; NOT a real observation and "
                    "creates no external evidence",
        }


@dataclass
class InternalSimulation:
    """Runs bounded internal simulations over signs (output marked non-real)."""

    max_steps: int = 8

    def simulate_sequence(self, signs: List[str], scope: str,
                          *, evidence_refs: List[str] = None) -> SimulationResult:
        result = SimulationResult(scope=scope,
                                  evidence_refs=list(evidence_refs or []))
        for i, sref in enumerate(signs[:self.max_steps]):
            result.steps.append(SimulationStep(
                index=i, sign_ref=sref,
                note=f"simulated step over {sref}"))
        result.usefulness = round(min(1.0, 0.1 * len(result.steps)), 4)
        result.seeds_hypothesis = len(result.steps) >= 2
        return result

    def simulate_absence(self, sign_ref: str,
                         *, evidence_refs: List[str] = None) -> SimulationResult:
        result = SimulationResult(scope=SimulationScope.ABSENCE_WINDOW,
                                  evidence_refs=list(evidence_refs or []))
        result.steps.append(SimulationStep(
            index=0, sign_ref=sign_ref,
            note=f"simulated absence of {sign_ref}"))
        result.usefulness = 0.3
        result.seeds_hypothesis = True
        return result
