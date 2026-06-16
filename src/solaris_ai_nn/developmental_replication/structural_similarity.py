"""Structural similarity -- how alike are two runs' observable structures?

:class:`StructuralSimilarity` scores per-dimension similarity between two runs
(sensorium adaptation, concept/sign families, cognition, prediction trajectory,
action-effect learning, habit formation, source diet, boundary, contamination,
plateau/regression, growth-vs-accumulation). Similarity is *structural*, not
subjective, and never implies consciousness. Low similarity may be real
divergence, noise, or insufficient evidence; high similarity may be robust
development OR fixture overfit -- both must be considered.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .cross_run_alignment import _jaccard, _numeric


class StructuralSimilarityMetric:
    SENSORIUM_ADAPTATION = "sensorium_adaptation_similarity"
    CONCEPT_FAMILY = "concept_family_similarity"
    SIGN_FAMILY = "sign_family_similarity"
    COGNITION_PROFILE = "cognition_profile_similarity"
    PREDICTION_TRAJECTORY = "prediction_trajectory_similarity"
    ACTION_EFFECT_LEARNING = "action_effect_learning_similarity"
    HABIT_FORMATION = "habit_formation_similarity"
    SOURCE_DIET = "source_diet_similarity"
    BOUNDARY_PROFILE = "boundary_profile_similarity"
    CONTAMINATION_PROFILE = "contamination_profile_similarity"
    PLATEAU_REGRESSION = "plateau_regression_similarity"
    GROWTH_VS_ACCUMULATION = "growth_vs_accumulation_similarity"

    ALL = (SENSORIUM_ADAPTATION, CONCEPT_FAMILY, SIGN_FAMILY, COGNITION_PROFILE,
           PREDICTION_TRAJECTORY, ACTION_EFFECT_LEARNING, HABIT_FORMATION,
           SOURCE_DIET, BOUNDARY_PROFILE, CONTAMINATION_PROFILE,
           PLATEAU_REGRESSION, GROWTH_VS_ACCUMULATION)


@dataclass
class StructuralSimilarityResult:
    """Per-dimension + overall structural similarity, with caveats."""

    run_a: str
    run_b: str
    scores: Dict[str, float] = field(default_factory=dict)
    overall: float = 0.0
    measured_dimensions: int = 0
    caveats: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_a": self.run_a, "run_b": self.run_b,
            "scores": {k: round(v, 4) for k, v in self.scores.items()},
            "overall": round(self.overall, 4),
            "measured_dimensions": self.measured_dimensions,
            "caveats": list(self.caveats),
            "note": "structural similarity only; does not imply consciousness",
        }


def _num_sim(a: Any, b: Any) -> float:
    na, nb = _numeric(a), _numeric(b)
    if na is None or nb is None:
        return None
    denom = max(abs(na), abs(nb), 1.0)
    return max(0.0, 1.0 - abs(na - nb) / denom)


@dataclass
class StructuralSimilarity:
    """Computes structural similarity between two runs (conservatively)."""

    def compare(self, run_a: Dict[str, Any], run_b: Dict[str, Any],
                ) -> StructuralSimilarityResult:
        da, db = (run_a.get("developmental_profile", {}),
                  run_b.get("developmental_profile", {}))
        sa, sb = run_a.get("world_signature", {}), run_b.get("world_signature",
                                                             {})
        ma, mb = run_a.get("stack_metrics", {}), run_b.get("stack_metrics", {})

        candidates = {
            StructuralSimilarityMetric.SENSORIUM_ADAPTATION:
                _num_sim(da.get("composite_growth"), db.get("composite_growth")),
            StructuralSimilarityMetric.CONCEPT_FAMILY: _family_sim(
                sa.get("concept_family_distribution")
                or ma.get("concept_family_distribution"),
                sb.get("concept_family_distribution")
                or mb.get("concept_family_distribution")),
            StructuralSimilarityMetric.SIGN_FAMILY: _family_sim(
                sa.get("sign_family_distribution")
                or ma.get("sign_family_distribution"),
                sb.get("sign_family_distribution")
                or mb.get("sign_family_distribution")),
            StructuralSimilarityMetric.COGNITION_PROFILE: _family_sim(
                sa.get("cognitive_move_distribution"),
                sb.get("cognitive_move_distribution")),
            StructuralSimilarityMetric.PREDICTION_TRAJECTORY: _num_sim(
                da.get("durable_prediction_improvement_score"),
                db.get("durable_prediction_improvement_score")),
            StructuralSimilarityMetric.ACTION_EFFECT_LEARNING: _num_sim(
                da.get("durable_action_effect_learning_score"),
                db.get("durable_action_effect_learning_score")),
            StructuralSimilarityMetric.HABIT_FORMATION: _family_sim(
                sa.get("habit_profile") or ma.get("habit_profile"),
                sb.get("habit_profile") or mb.get("habit_profile")),
            StructuralSimilarityMetric.SOURCE_DIET: _family_sim(
                run_a.get("source_diet"), run_b.get("source_diet")),
            StructuralSimilarityMetric.BOUNDARY_PROFILE: _num_sim(
                sa.get("boundary_clarity_score"),
                sb.get("boundary_clarity_score")),
            StructuralSimilarityMetric.CONTAMINATION_PROFILE: _num_sim(
                sa.get("human_label_contamination_score"),
                sb.get("human_label_contamination_score")),
            StructuralSimilarityMetric.PLATEAU_REGRESSION: _num_sim(
                _sum(da.get("plateau_count"), da.get("regression_count")),
                _sum(db.get("plateau_count"), db.get("regression_count"))),
            StructuralSimilarityMetric.GROWTH_VS_ACCUMULATION:
                1.0 if da.get("structural_growth_status")
                == db.get("structural_growth_status")
                and da.get("structural_growth_status") is not None else
                (0.0 if da.get("structural_growth_status") is not None
                 and db.get("structural_growth_status") is not None else None),
        }
        scores = {k: v for k, v in candidates.items() if v is not None}
        result = StructuralSimilarityResult(
            run_a=run_a.get("run_id"), run_b=run_b.get("run_id"), scores=scores,
            measured_dimensions=len(scores))
        result.overall = (sum(scores.values()) / len(scores)) if scores else 0.0
        self._add_caveats(result, run_a, run_b)
        return result

    @staticmethod
    def _add_caveats(result: StructuralSimilarityResult, run_a, run_b) -> None:
        if result.measured_dimensions < 3:
            result.caveats.append(
                "few measurable dimensions; similarity is low-confidence / "
                "insufficient evidence")
        if result.overall >= 0.85:
            both_fixture = (run_a.get("fixture_live_replay") == "fixture"
                            and run_b.get("fixture_live_replay") == "fixture")
            if both_fixture:
                result.caveats.append(
                    "very high similarity on fixtures may indicate robust "
                    "development OR fixture overfit; both must be considered")
        if result.overall <= 0.3 and result.measured_dimensions >= 3:
            result.caveats.append(
                "low similarity may indicate real divergence, noise, or "
                "insufficient evidence; it does not by itself mean failure")


def _family_sim(a, b):
    if not isinstance(a, dict) or not isinstance(b, dict):
        return None
    if not a and not b:
        return None
    return _jaccard(a, b)


def _sum(*vals):
    nums = [v for v in vals if isinstance(v, (int, float))]
    return float(sum(nums)) if nums else None
