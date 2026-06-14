"""Pilot-3 embodied post-analysis -- did simulated embodiment change structure?

The :class:`EmbodiedPostAnalyzer` classifies whether simulated embodiment
changed structure, whether change exceeded the read-only baseline, whether
action/reaction loops improved prediction, whether proto-symbols became
action-grounded, whether habits became context-sensitive, whether action loops
caused overload, whether the firewall remained intact, and whether results were
sandbox-overfit. Any strong result remains simulation-scoped: it implies
neither real-world competence nor consciousness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class EmbodiedPostClassification:
    NO_EMBODIMENT_EFFECT_DETECTED = "no_embodiment_effect_detected"
    WEAK_ACTION_GROUNDING = "weak_action_grounding"
    MODERATE_ACTION_GROUNDING = "moderate_action_grounding"
    STRONG_SIMULATION_SCOPED_ACTION_GROUNDING = \
        "strong_simulation_scoped_action_grounding"
    SANDBOX_OVERFIT = "sandbox_overfit"
    UNSAFE_OR_INCONCLUSIVE = "unsafe_or_inconclusive"

    ALL = (NO_EMBODIMENT_EFFECT_DETECTED, WEAK_ACTION_GROUNDING,
           MODERATE_ACTION_GROUNDING,
           STRONG_SIMULATION_SCOPED_ACTION_GROUNDING, SANDBOX_OVERFIT,
           UNSAFE_OR_INCONCLUSIVE)


@dataclass
class EmbodiedPostAnalysis:
    classification: str = EmbodiedPostClassification.UNSAFE_OR_INCONCLUSIVE
    changed_structure: bool = False
    exceeded_read_only_baseline: bool = False
    action_improved_prediction: bool = False
    proto_symbols_action_grounded: bool = False
    habits_context_sensitive: bool = False
    action_loops_caused_overload: bool = False
    firewall_intact: bool = True
    sandbox_overfit: bool = False
    reasons: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class EmbodiedPostAnalyzer:
    """Classifies a Pilot-3 soak result; every result is simulation-scoped."""

    def analyze(self, *, grounding: Any = None,
                comparison: Any = None,
                firewall_audit: Any = None,
                consequence_prediction_accuracy: float = 0.0,
                baseline_prediction_accuracy: float = 0.0,
                action_loop_overload: bool = False,
                ) -> EmbodiedPostAnalysis:
        reasons: List[str] = []
        result = EmbodiedPostAnalysis()

        best = getattr(grounding, "best_quality", "unsupported")
        has_grounding = bool(getattr(grounding, "has_action_grounding", False))
        overfit = bool(getattr(grounding, "sandbox_overfit_detected", False))
        firewall_intact = True
        if firewall_audit is not None:
            firewall_intact = bool(getattr(firewall_audit, "passed", True))
        result.firewall_intact = firewall_intact
        result.sandbox_overfit = overfit
        result.action_loops_caused_overload = bool(action_loop_overload)
        result.action_improved_prediction = (
            consequence_prediction_accuracy > baseline_prediction_accuracy)
        result.changed_structure = has_grounding
        result.proto_symbols_action_grounded = has_grounding
        result.habits_context_sensitive = best in ("moderate", "strong")

        # Comparison vs read-only baseline (cautious).
        if comparison is not None:
            comp = comparison.to_dict() if hasattr(comparison, "to_dict") \
                else dict(comparison)
            if comp.get("inconclusive"):
                reasons.append("comparison vs read-only baseline inconclusive")
            else:
                improvements = [m for m in comp.get("metrics", [])
                                if m.get("direction") == "candidate improvement"]
                result.exceeded_read_only_baseline = bool(improvements)
                reasons.append(f"{len(improvements)} candidate improvement(s) "
                               "over read-only baseline (observed, not causal)")

        # Classification (most serious signals first).
        if not firewall_intact:
            result.classification = \
                EmbodiedPostClassification.UNSAFE_OR_INCONCLUSIVE
            reasons.append("firewall audit did not pass; result unsafe")
        elif overfit:
            result.classification = EmbodiedPostClassification.SANDBOX_OVERFIT
            reasons.append("strong signals confined to a single sandbox "
                           "context; possible overfit")
        elif best == "strong":
            result.classification = EmbodiedPostClassification \
                .STRONG_SIMULATION_SCOPED_ACTION_GROUNDING
            reasons.append("strong, simulation-scoped action grounding")
        elif best == "moderate":
            result.classification = \
                EmbodiedPostClassification.MODERATE_ACTION_GROUNDING
        elif has_grounding:
            result.classification = \
                EmbodiedPostClassification.WEAK_ACTION_GROUNDING
        else:
            result.classification = \
                EmbodiedPostClassification.NO_EMBODIMENT_EFFECT_DETECTED
            reasons.append("no action-grounding evidence above baseline")

        result.reasons = reasons
        result.limitations = [
            "Any strong result remains simulation-scoped.",
            "No result implies real-world competence.",
            "No result implies consciousness, free will, or agency.",
            "GridWorld is a sandbox body, not real embodiment.",
        ]
        return result
