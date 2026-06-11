"""Prospection -- bounded, approximate consequence estimates. Never acts.

Each candidate gets a one-step (default) estimate of expected valence, risk,
and energy cost, assembled from whatever evidence the context offers: world
model action->valence support, habit weights, the anticipation tracker, and
(for embodied candidates) a deep-copied GridWorld sandbox. Insufficient data
returns "unknown" with low confidence -- consequences are never invented,
and every result is marked as a simulated estimate.
"""

from __future__ import annotations

import copy
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .action_candidates import ActionCandidate, ActionCandidateType

DEFAULT_HORIZON = 1
MAX_HORIZON = 3


@dataclass
class ProspectiveScenario:
    """One simulated step inside a prospection."""

    step: int
    label: str
    expected_valence: Optional[float] = None
    expected_risk: float = 0.0
    expected_cost: float = 0.0
    basis: str = ""
    simulated: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class ProspectionResult:
    """The estimate, with its confidence and evidence basis."""

    label: str
    outcome: str = "unknown"  # favorable | unfavorable | neutral | unknown
    expected_valence: Optional[float] = None
    expected_risk: float = 0.0
    expected_cost: float = 0.0
    confidence: float = 0.0
    horizon: int = DEFAULT_HORIZON
    scenarios: List[ProspectiveScenario] = field(default_factory=list)
    basis: List[str] = field(default_factory=list)
    simulated: bool = True  # an estimate, never a fact
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {**{k: v for k, v in self.__dict__.items()
                   if k != "scenarios"},
                "scenarios": [s.to_dict() for s in self.scenarios]}


@dataclass
class ProspectionEngine:
    """Estimates candidate consequences from available evidence."""

    simulations_total: int = field(default=0, init=False)
    unknown_total: int = field(default=0, init=False)
    last_results: List[Dict[str, Any]] = field(default_factory=list,
                                               init=False)

    # -- single candidate ---------------------------------------------------------

    def simulate_candidate(self, candidate: ActionCandidate,
                           context: Optional[Dict[str, Any]] = None,
                           horizon: int = DEFAULT_HORIZON,
                           ) -> ProspectionResult:
        ctx = context or {}
        horizon = max(1, min(int(horizon), MAX_HORIZON))
        label = candidate.label
        basis: List[str] = []
        valence: Optional[float] = None

        # 1. World-model support: action -> valence edges, if provided.
        world = ctx.get("world_model_valence") or {}
        if label in world:
            valence = float(world[label])
            basis.append(f"world model: {label!r} produced valence "
                         f"{valence:+.2f} historically")
        # 2. Habit weights as weak evidence.
        habit = (ctx.get("habit_weights") or {}).get(label)
        if habit is not None:
            habit_valence = max(-1.0, min(1.0, float(habit)))
            valence = (habit_valence if valence is None
                       else 0.7 * valence + 0.3 * habit_valence)
            basis.append(f"habit weight {habit:+.2f}")
        # 3. Embodied sandbox: deep-copied world, real state untouched.
        world_obj = ctx.get("grid_world")
        if world_obj is not None and candidate.action_type \
                == ActionCandidateType.SIMULATED_EMBODIED_ACTION:
            risk = self._sandbox_risk(world_obj, ctx.get("position"), label)
            candidate_risk = max(candidate.expected_risk, risk)
            basis.append(f"GridWorld sandbox risk estimate {risk:.2f}")
        else:
            candidate_risk = candidate.expected_risk
        # 4. Anticipation tracker as a generic confidence prior.
        anticipation = ctx.get("anticipation_accuracy")
        if anticipation is not None:
            basis.append(f"anticipation accuracy {anticipation:.2f}")

        scenarios = [ProspectiveScenario(
            step=1, label=label, expected_valence=valence,
            expected_risk=candidate_risk,
            expected_cost=candidate.expected_cost,
            basis="; ".join(basis) or "no evidence")]

        if not basis:
            self.unknown_total += 1
            result = ProspectionResult(
                label=label, outcome="unknown", confidence=0.1,
                horizon=horizon, scenarios=scenarios,
                basis=["insufficient data: no world-model, habit, or "
                       "sandbox evidence; consequences are not invented"])
        else:
            outcome = ("favorable" if (valence or 0.0) > 0.1
                       and candidate_risk < 0.5
                       else "unfavorable" if (valence or 0.0) < -0.1
                       or candidate_risk >= 0.7 else "neutral")
            confidence = round(min(0.85, 0.25 * len(basis)
                                   + 0.2 * float(anticipation or 0.0)), 4)
            result = ProspectionResult(
                label=label, outcome=outcome, expected_valence=valence,
                expected_risk=round(candidate_risk, 4),
                expected_cost=candidate.expected_cost,
                confidence=confidence, horizon=horizon,
                scenarios=scenarios, basis=basis)
        self.simulations_total += 1
        self.last_results.append(result.to_dict())
        self.last_results = self.last_results[-50:]
        return result

    @staticmethod
    def _sandbox_risk(world: Any, position: Any, label: str) -> float:
        """Estimate movement risk in a deep copy; never touch the original."""
        try:
            sandbox = copy.deepcopy(world)
        except Exception:
            return 0.0
        nearest_danger = None
        if hasattr(sandbox, "nearest"):
            from ..embodiment.grid_world import DANGER

            hit = sandbox.nearest(DANGER, pos=position) \
                if position is not None else sandbox.nearest(DANGER)
            if hit is not None:
                nearest_danger = hit[2]
        if nearest_danger is None:
            return 0.0
        if label in ("approach_reward", "explore_safely", "seek_signal") \
                or label.startswith("move"):
            return round(max(0.0, min(1.0, 1.5 / (nearest_danger + 0.5))), 4)
        return 0.05  # rest/look style actions carry minimal risk

    # -- sequences ------------------------------------------------------------------

    def simulate_sequence(self, sequence: List[Any],
                          context: Optional[Dict[str, Any]] = None,
                          horizon: int = MAX_HORIZON) -> ProspectionResult:
        """Chain per-step estimates with decaying confidence."""
        ctx = context or {}
        steps = list(sequence)[:max(1, min(int(horizon), 5))]
        scenarios: List[ProspectiveScenario] = []
        total_valence = 0.0
        valence_count = 0
        total_risk = 0.0
        total_cost = 0.0
        confidence = 1.0
        basis: List[str] = []
        for index, step in enumerate(steps, start=1):
            candidate = (step if isinstance(step, ActionCandidate)
                         else ActionCandidate(
                             action_type=ActionCandidateType
                             .SIMULATED_EMBODIED_ACTION,
                             label=str(getattr(step, "label", step)),
                             executable_scope="simulation_only"))
            result = self.simulate_candidate(candidate, ctx, horizon=1)
            scenario = result.scenarios[0]
            scenario.step = index
            scenarios.append(scenario)
            if result.expected_valence is not None:
                total_valence += result.expected_valence
                valence_count += 1
            total_risk = max(total_risk, result.expected_risk)
            total_cost += result.expected_cost
            confidence *= max(0.2, result.confidence)  # decays with depth
            basis.extend(result.basis[:1])
        mean_valence = (total_valence / valence_count
                        if valence_count else None)
        outcome = ("unknown" if mean_valence is None
                   else "favorable" if mean_valence > 0.1
                   and total_risk < 0.5
                   else "unfavorable" if mean_valence < -0.1
                   or total_risk >= 0.7 else "neutral")
        return ProspectionResult(
            label=" -> ".join(s.label for s in scenarios),
            outcome=outcome, expected_valence=mean_valence,
            expected_risk=round(total_risk, 4),
            expected_cost=round(total_cost, 4),
            confidence=round(confidence, 4), horizon=len(scenarios),
            scenarios=scenarios, basis=basis)

    def compare_candidates(self, candidates: List[ActionCandidate],
                           context: Optional[Dict[str, Any]] = None,
                           ) -> Dict[str, Dict[str, Any]]:
        """label -> prospection summary, ready for the arbitrator."""
        out: Dict[str, Dict[str, Any]] = {}
        for candidate in candidates:
            result = self.simulate_candidate(candidate, context)
            out[candidate.label] = {
                "outcome": result.outcome,
                "expected_valence": result.expected_valence or 0.0,
                "expected_risk": result.expected_risk,
                "confidence": result.confidence,
            }
        return out

    def snapshot(self) -> Dict[str, Any]:
        return {
            "simulations_total": self.simulations_total,
            "unknown_total": self.unknown_total,
            "recent": self.last_results[-5:],
            "note": "prospection results are simulated estimates with "
                    "confidence, never facts; nothing is executed",
        }
