"""Hypothesis priority -- which candidate to test first, and whether to test.

The :class:`HypothesisPrioritizer` scores hypotheses by expected information
gain, the pressure that motivated them, and testability, minus safety risk
and cost. Low-risk, high-information tests rank higher; unsafe hypotheses are
never scheduled; and an emergency or critical ops state blocks all testing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .hypotheses import Hypothesis, HypothesisStatus, HypothesisType

# Per-type pressure relevance (how urgent this family tends to be).
_TYPE_RELEVANCE = {
    HypothesisType.MYSTERIUM_REDUCTION: 0.9,
    HypothesisType.PREDICTION: 0.7,
    HypothesisType.WORLD_MODEL_EDGE: 0.7,
    HypothesisType.PROTO_SYMBOL_GROUNDING: 0.6,
    HypothesisType.DELAYED_CONSEQUENCE: 0.6,
    HypothesisType.CAUSAL_CANDIDATE: 0.6,
    HypothesisType.STAGNATION_RECOVERY: 0.6,
    HypothesisType.ANOMALY_PATTERN: 0.5,
    HypothesisType.PROTO_SYNTAX: 0.5,
    HypothesisType.EXECUTIVE_ARBITRATION: 0.4,
    HypothesisType.HOMEOSTATIC_REGULATION: 0.4,
    HypothesisType.BOUNDARY: 0.4,
    HypothesisType.HABIT_CONTEXT: 0.4,
}

_RISK_PENALTY = {"low": 0.0, "medium": 0.2, "high": 0.5}


@dataclass
class HypothesisPrioritizer:
    """Scores and ranks hypotheses; refuses to schedule the unsafe."""

    def testing_blocked(self, context: Dict[str, Any]) -> bool:
        ctx = dict(context or {})
        return bool(ctx.get("emergency")
                    or ctx.get("emergency_stop_requested")
                    or ctx.get("health_level") == "critical")

    def score(self, hypothesis: Hypothesis,
              context: Dict[str, Any]) -> float:
        if not hypothesis.testable \
                or hypothesis.status == HypothesisStatus.UNSAFE_TO_TEST:
            return 0.0
        ctx = dict(context or {})
        relevance = _TYPE_RELEVANCE.get(hypothesis.type, 0.4)
        # Uncertainty is information potential; high uncertainty = worth it.
        info_potential = hypothesis.uncertainty
        # Current global pressure boosts pressure-relevant families.
        mysterium = float(ctx.get("mysterium_pressure", 0.0) or 0.0)
        boost = (mysterium * 0.3
                 if hypothesis.type == HypothesisType.MYSTERIUM_REDUCTION
                 else 0.0)
        risk_penalty = _RISK_PENALTY.get(hypothesis.risk_level, 0.2)
        cost = float(hypothesis.metadata.get("expected_cost", 0.1) or 0.1)
        score = (0.5 * relevance + 0.3 * info_potential + boost
                 - risk_penalty - 0.1 * cost)
        return round(max(0.0, min(1.0, score)), 4)

    def prioritize(self, hypotheses: List[Hypothesis],
                   context: Dict[str, Any]) -> List[Hypothesis]:
        if self.testing_blocked(context):
            for h in hypotheses:
                h.priority = 0.0
            return []
        scored = []
        for h in hypotheses:
            h.priority = self.score(h, context)
            if h.priority > 0.0 \
                    and h.status not in HypothesisStatus.CLOSED \
                    and h.status != HypothesisStatus.UNSAFE_TO_TEST:
                scored.append(h)
        scored.sort(key=lambda h: h.priority, reverse=True)
        return scored

    def snapshot(self) -> Dict[str, Any]:
        return {"risk_penalties": dict(_RISK_PENALTY)}
