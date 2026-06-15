"""Comparative analysis -- structural differences between sensorium arms.

:class:`SensoriumComparison` compares pairs of arms across eight structural
dimensions (proto-symbol distribution, world-model topology, hypothesis family,
LOGOS tension, attention strategy, changed-perception, grounding, contamination)
and assigns a :class:`DifferenceStrength`. Differences are structural, never
metaphysical; missing data yields ``inconclusive``; and a negative (no-difference)
result is preserved, not discarded.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


class DifferenceStrength:
    NONE = "none"
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    INCONCLUSIVE = "inconclusive"

    ALL = (NONE, WEAK, MODERATE, STRONG, INCONCLUSIVE)
    ORDER = {INCONCLUSIVE: -1, NONE: 0, WEAK: 1, MODERATE: 2, STRONG: 3}


# The canonical comparison pairs (by arm_id), plus a human label.
_PAIRS = (
    ("human_like", "non_human", "human-like-only vs non-human-only"),
    ("human_like", "mixed", "human-like-only vs mixed"),
    ("non_human", "mixed", "non-human-only vs mixed"),
    ("feature_only", "human_labelled", "feature-only vs human-labelled"),
    ("passive", "adaptive", "passive parser vs adaptive receptor field"),
    ("absence_heavy", "non_human", "absence-heavy vs normal rhythm"),
)


@dataclass
class SensoriumDifference:
    arm_a: str
    arm_b: str
    title: str
    dimension_scores: Dict[str, float] = field(default_factory=dict)
    overall_score: float = 0.0
    strength: str = DifferenceStrength.NONE
    reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass
class SensoriumComparisonResult:
    differences: List[SensoriumDifference] = field(default_factory=list)
    strongest: Optional[str] = None
    inconclusive_count: int = 0
    negative_result_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "differences": [d.to_dict() for d in self.differences],
            "strongest": self.strongest,
            "inconclusive_count": self.inconclusive_count,
            "negative_result_count": self.negative_result_count,
            "note": "structural differences only; not a ranking and not a "
                    "metaphysical comparison",
        }


@dataclass
class SensoriumComparison:
    """Builds the pairwise comparison across a study's arm results."""

    def compare(self, arm_results: Dict[str, Dict[str, Any]],
                ) -> SensoriumComparisonResult:
        result = SensoriumComparisonResult()
        for a_id, b_id, title in _PAIRS:
            a = arm_results.get(a_id)
            b = arm_results.get(b_id)
            diff = self._compare_pair(a_id, b_id, title, a, b)
            result.differences.append(diff)
            if diff.strength == DifferenceStrength.INCONCLUSIVE:
                result.inconclusive_count += 1
            elif diff.strength == DifferenceStrength.NONE:
                result.negative_result_count += 1
        ranked = [d for d in result.differences
                  if d.strength not in (DifferenceStrength.INCONCLUSIVE,)]
        if ranked:
            best = max(ranked,
                       key=lambda d: DifferenceStrength.ORDER[d.strength])
            result.strongest = f"{best.arm_a} vs {best.arm_b}: {best.strength}"
        return result

    def _compare_pair(self, a_id: str, b_id: str, title: str,
                      a: Optional[Dict[str, Any]],
                      b: Optional[Dict[str, Any]]) -> SensoriumDifference:
        diff = SensoriumDifference(arm_a=a_id, arm_b=b_id, title=title)
        if a is None or b is None or a.get("blocked") or b.get("blocked") \
                or a.get("inconclusive") or b.get("inconclusive"):
            diff.strength = DifferenceStrength.INCONCLUSIVE
            diff.reasons.append("one or both arms missing/blocked/inconclusive")
            return diff
        ma, mb = a["metrics"], b["metrics"]
        scores = {
            "proto_symbol_distribution": self._delta(
                ma.get("symbol_family_diversity", 0),
                mb.get("symbol_family_diversity", 0), 5.0),
            "world_model_topology": self._delta(
                ma.get("world_node_count", 0), mb.get("world_node_count", 0),
                20.0),
            "hypothesis_family": self._delta(
                ma.get("hypothesis_count", 0), mb.get("hypothesis_count", 0),
                20.0),
            "logos_tension": self._delta(
                ma.get("absence_pressure_mean", 0.0),
                mb.get("absence_pressure_mean", 0.0), 1.0),
            "attention_strategy": self._delta(
                ma.get("attention_priority_delta", 0.0),
                mb.get("attention_priority_delta", 0.0), 50.0),
            "changed_perception": self._delta(
                ma.get("changed_perception_score", 0.0),
                mb.get("changed_perception_score", 0.0), 1.0),
            "grounding": self._delta(
                ma.get("modality_native_grounding_score", 0.0),
                mb.get("modality_native_grounding_score", 0.0), 1.0),
            "contamination": self._delta(
                ma.get("human_label_contamination_score", 0.0),
                mb.get("human_label_contamination_score", 0.0), 1.0),
        }
        diff.dimension_scores = {k: round(v, 4) for k, v in scores.items()}
        overall = sum(scores.values()) / len(scores)
        diff.overall_score = round(overall, 4)
        diff.strength = self._strength(overall)
        if diff.strength == DifferenceStrength.NONE:
            diff.reasons.append("no meaningful structural difference detected "
                                "(negative result preserved)")
        return diff

    @staticmethod
    def _delta(a: float, b: float, scale: float) -> float:
        return min(1.0, abs(float(a) - float(b)) / scale) if scale else 0.0

    @staticmethod
    def _strength(overall: float) -> str:
        if overall >= 0.4:
            return DifferenceStrength.STRONG
        if overall >= 0.2:
            return DifferenceStrength.MODERATE
        if overall >= 0.05:
            return DifferenceStrength.WEAK
        return DifferenceStrength.NONE
