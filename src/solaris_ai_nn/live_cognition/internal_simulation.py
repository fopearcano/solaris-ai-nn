"""Live internal simulation -- bounded offline metadata; controls nothing.

:class:`LiveInternalSimulation` rolls a small, step-bounded internal scenario from an
anticipation (expected source sequence, absence/rhythm continuation, overload/
deprivation scenario, co-occurrence, contradiction). It is offline metadata only: it
controls no feeders or sources, executes no commands, is bounded by ``max_steps``,
preserves uncertainty, and is meant to be compared against later observed events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class SimulationStatus:
    PROPOSED = "proposed"
    MATCHED = "matched"
    CONTRADICTED = "contradicted"
    NOT_YET_OBSERVED = "not_yet_observed"
    CONTAMINATED = "contaminated"
    UNKNOWN = "unknown"

    ALL = (PROPOSED, MATCHED, CONTRADICTED, NOT_YET_OBSERVED, CONTAMINATED,
           UNKNOWN)


class SimulationKind:
    EXPECTED_SOURCE_SEQUENCE = "expected_source_sequence"
    EXPECTED_ABSENCE_CONTINUATION = "expected_absence_continuation"
    EXPECTED_RHYTHM_CONTINUATION = "expected_rhythm_continuation"
    OVERLOAD_SCENARIO = "overload_scenario"
    DEPRIVATION_SCENARIO = "deprivation_scenario"
    CO_OCCURRENCE_SCENARIO = "co_occurrence_scenario"
    CONTRADICTION_SCENARIO = "contradiction_scenario"
    UNKNOWN = "unknown_scenario"

    ALL = (EXPECTED_SOURCE_SEQUENCE, EXPECTED_ABSENCE_CONTINUATION,
           EXPECTED_RHYTHM_CONTINUATION, OVERLOAD_SCENARIO, DEPRIVATION_SCENARIO,
           CO_OCCURRENCE_SCENARIO, CONTRADICTION_SCENARIO, UNKNOWN)

_ANTICIPATION_TO_KIND = {
    "rhythm_continuation": SimulationKind.EXPECTED_RHYTHM_CONTINUATION,
    "source_silence_likely_continues":
        SimulationKind.EXPECTED_ABSENCE_CONTINUATION,
    "recurrence_expected": SimulationKind.EXPECTED_SOURCE_SEQUENCE,
    "co_occurrence_expected": SimulationKind.CO_OCCURRENCE_SCENARIO,
    "overload_risk_expected": SimulationKind.OVERLOAD_SCENARIO,
    "deprivation_risk_expected": SimulationKind.DEPRIVATION_SCENARIO,
    "next_source_likely_active": SimulationKind.EXPECTED_SOURCE_SEQUENCE,
    "contrast_expected": SimulationKind.CONTRADICTION_SCENARIO,
}


@dataclass
class SimulationCandidate:
    """One bounded internal simulation rollout (offline metadata only)."""

    simulation_id: str
    kind: str
    sign_id: str
    steps: List[str] = field(default_factory=list)
    uncertainty: float = 1.0
    status: str = SimulationStatus.PROPOSED
    contamination_findings: List[str] = field(default_factory=list)

    @property
    def step_count(self) -> int:
        return len(self.steps)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "simulation_id": self.simulation_id, "kind": self.kind,
            "sign_id": self.sign_id, "step_count": self.step_count,
            "steps": list(self.steps), "uncertainty": round(self.uncertainty, 3),
            "status": self.status,
            "contamination_findings": list(self.contamination_findings),
            "controls_feeders": False, "executes_commands": False,
            "acts_in_world": False, "is_offline_metadata": True,
        }


@dataclass
class LiveInternalSimulation:
    """Builds bounded offline simulations from anticipations."""

    max_steps: int = 8

    def simulate(self, anticipations: List[Any], *, max_simulations: int = 100,
                 ) -> List[SimulationCandidate]:
        out: List[SimulationCandidate] = []
        for i, ant in enumerate(anticipations):
            if len(out) >= max_simulations:
                break
            d = ant.to_dict() if hasattr(ant, "to_dict") else dict(ant)
            if d.get("status") in ("contaminated", "blocked"):
                continue
            kind = _ANTICIPATION_TO_KIND.get(d.get("anticipation_type"),
                                             SimulationKind.UNKNOWN)
            sim = SimulationCandidate(
                simulation_id=f"sim_{i}", kind=kind,
                sign_id=d.get("sign_id", ""),
                uncertainty=float(d.get("uncertainty", 1.0)),
                contamination_findings=list(
                    d.get("contamination_findings", []) or []))
            # Bounded rollout: at most max_steps descriptive steps.
            n = min(self.max_steps, 3 + i % 3)
            sim.steps = [f"step {k + 1}: expected {kind} continues "
                         f"(uncertainty {sim.uncertainty:.2f})"
                         for k in range(n)]
            sim.status = SimulationStatus.NOT_YET_OBSERVED
            out.append(sim)
        return out
