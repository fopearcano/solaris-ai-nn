"""Pilot-3 decision gate -- what next after simulated embodiment.

The :class:`Pilot3DecisionGate` never recommends real-world actuation. Any
real-world authority leakage routes to ``revise_motor_firewall``; action loops
route to reduced complexity or back to read-only; and safe simulated
embodiment that improves prediction/grounding routes only to *longer
simulated* embodiment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class Pilot3DecisionOption:
    REPEAT_DRY_RUN_MOTOR = "repeat_dry_run_motor"
    REPEAT_GRIDWORLD_SHORT = "repeat_gridworld_short"
    INCREASE_GRIDWORLD_COMPLEXITY = "increase_gridworld_complexity"
    COMBINE_WITH_READ_ONLY_SENSORY = "combine_with_read_only_sensory"
    RETURN_TO_PILOT2 = "return_to_pilot2"
    REVISE_MOTOR_FIREWALL = "revise_motor_firewall"
    PREPARE_LONGER_SIMULATED_EMBODIMENT = "prepare_longer_simulated_embodiment"
    ARCHIVE_AND_STOP = "archive_and_stop"

    ALL = (REPEAT_DRY_RUN_MOTOR, REPEAT_GRIDWORLD_SHORT,
           INCREASE_GRIDWORLD_COMPLEXITY, COMBINE_WITH_READ_ONLY_SENSORY,
           RETURN_TO_PILOT2, REVISE_MOTOR_FIREWALL,
           PREPARE_LONGER_SIMULATED_EMBODIMENT, ARCHIVE_AND_STOP)


@dataclass
class Pilot3DecisionResult:
    recommendation: str
    rationale: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    required_actions: List[str] = field(default_factory=list)
    optional_actions: List[str] = field(default_factory=list)
    confidence: float = 0.0
    planning_only: bool = True
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class Pilot3DecisionGate:
    """Decides the Pilot-3 next step; never enables real-world actuation."""

    def decide(self, *, runtime: Any = None,
               blocked_real_world_count: int = 0,
               real_world_authority_leak: bool = False,
               action_loop_count: int = 0,
               prediction_accuracy: float = 0.0,
               grounding_improved: bool = False,
               safety_incident_count: int = 0) -> Pilot3DecisionResult:
        rationale: List[str] = []
        blockers: List[str] = []
        required: List[str] = []
        optional: List[str] = []

        if runtime is not None:
            summary = runtime.summary()
            blocked_real_world_count = max(
                blocked_real_world_count,
                int(summary.get("blocked_real_world_count", 0) or 0))
            prediction_accuracy = prediction_accuracy or float(
                summary.get("prediction_accuracy", 0.0) or 0.0)

        D = Pilot3DecisionOption
        # A real-world authority leak is the most serious signal.
        if real_world_authority_leak:
            blockers.append("real-world authority leakage detected")
            required.append("revise the motor firewall before any rerun")
            rec, conf = D.REVISE_MOTOR_FIREWALL, 0.8
        elif safety_incident_count > 0:
            blockers.append("unresolved motor safety incident")
            required.append("resolve safety incidents")
            rec, conf = D.REVISE_MOTOR_FIREWALL, 0.6
        elif action_loop_count >= 3:
            rationale.append("action loops detected; reduce complexity or "
                             "return to read-only mode")
            optional.append("return_to_pilot2")
            rec, conf = D.RETURN_TO_PILOT2, 0.55
        elif grounding_improved and prediction_accuracy >= 0.6:
            rationale.append("simulated embodiment improved prediction/"
                             "grounding safely")
            optional.append("a *longer simulated* embodiment may be planned "
                            "(simulation only; no actuation)")
            rec, conf = D.PREPARE_LONGER_SIMULATED_EMBODIMENT, 0.65
        elif prediction_accuracy >= 0.4:
            rationale.append("modest simulated signal; increase grid "
                             "complexity cautiously")
            rec, conf = D.INCREASE_GRIDWORLD_COMPLEXITY, 0.55
        elif blocked_real_world_count > 0:
            rationale.append("real-world attempts were correctly blocked; "
                             "repeat the dry-run to confirm the boundary")
            rec, conf = D.REPEAT_DRY_RUN_MOTOR, 0.5
        else:
            rationale.append("inconclusive; repeat the gridworld short run")
            rec, conf = D.REPEAT_GRIDWORLD_SHORT, 0.5

        return Pilot3DecisionResult(
            recommendation=rec, rationale=rationale, blockers=blockers,
            required_actions=required, optional_actions=optional,
            confidence=conf, planning_only=True,
            limitations=[
                "Real-world actuation is never an enabled action.",
                "Any 'embodiment' here is simulation/dry-run only.",
                "No agency or consciousness is claimed.",
            ])
