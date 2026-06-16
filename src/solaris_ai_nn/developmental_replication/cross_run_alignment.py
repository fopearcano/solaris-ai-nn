"""Cross-run alignment -- line up comparable structures across two runs.

:class:`CrossRunAlignment` aligns the observable structures of two runs
(epoch sequences, growth dimensions, maturation markers, phase transitions,
proto-concept/sign families, private syntax, prediction/action-effect/habit/
boundary/source-diet/contamination profiles, plateau/regression events, safety
blocks). Alignment preserves run-specific differences, never forces different
sensoriums into human labels, and reports partial/inconclusive when data is
missing. (Human glosses may be used as a debug overlay only, never as the
primary alignment key.)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


class AlignmentTarget:
    EPOCH_SEQUENCES = "epoch_sequences"
    GROWTH_DIMENSIONS = "growth_dimensions"
    MATURATION_MARKERS = "maturation_markers"
    PHASE_TRANSITIONS = "phase_transitions"
    PROTO_CONCEPT_FAMILIES = "proto_concept_families"
    SIGN_FAMILIES = "sign_families"
    PRIVATE_SYNTAX_DENSITY = "private_syntax_density"
    PREDICTION_PROFILES = "prediction_profiles"
    ACTION_EFFECT_PROFILES = "action_effect_profiles"
    HABIT_PROFILES = "habit_profiles"
    BOUNDARY_CLARITY_PROFILES = "boundary_clarity_profiles"
    SOURCE_DIET_PROFILES = "source_diet_profiles"
    CONTAMINATION_PROFILES = "contamination_profiles"
    PLATEAU_REGRESSION_EVENTS = "plateau_regression_events"
    SAFETY_BLOCKS = "safety_blocks"

    ALL = (EPOCH_SEQUENCES, GROWTH_DIMENSIONS, MATURATION_MARKERS,
           PHASE_TRANSITIONS, PROTO_CONCEPT_FAMILIES, SIGN_FAMILIES,
           PRIVATE_SYNTAX_DENSITY, PREDICTION_PROFILES, ACTION_EFFECT_PROFILES,
           HABIT_PROFILES, BOUNDARY_CLARITY_PROFILES, SOURCE_DIET_PROFILES,
           CONTAMINATION_PROFILES, PLATEAU_REGRESSION_EVENTS, SAFETY_BLOCKS)


class AlignmentStatus:
    ALIGNED = "aligned"
    PARTIAL = "partial"
    INCONCLUSIVE = "inconclusive"
    DIVERGENT = "divergent"

    ALL = (ALIGNED, PARTIAL, INCONCLUSIVE, DIVERGENT)


@dataclass
class AlignmentResult:
    """The alignment of one target across two runs."""

    target: str
    status: str
    overlap: float = 0.0
    detail: str = ""
    run_specific_differences: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"target": self.target, "status": self.status,
                "overlap": round(self.overlap, 4), "detail": self.detail,
                "run_specific_differences": list(self.run_specific_differences)}


# (run-field, key) extractor per target: where to read each structure from.
def _extract(run: Dict[str, Any], target: str) -> Any:
    dev = run.get("developmental_profile", {})
    soak = run.get("soak_profile", {})
    sig = run.get("world_signature", {})
    metrics = run.get("stack_metrics", {})
    table = {
        AlignmentTarget.EPOCH_SEQUENCES:
            dev.get("developmental_epoch_count"),
        AlignmentTarget.GROWTH_DIMENSIONS: dev.get("composite_growth"),
        AlignmentTarget.MATURATION_MARKERS:
            dev.get("maturation_marker_count"),
        AlignmentTarget.PHASE_TRANSITIONS:
            dev.get("phase_transition_count"),
        AlignmentTarget.PROTO_CONCEPT_FAMILIES:
            sig.get("concept_family_distribution")
            or metrics.get("concept_family_distribution"),
        AlignmentTarget.SIGN_FAMILIES:
            sig.get("sign_family_distribution")
            or metrics.get("sign_family_distribution"),
        AlignmentTarget.PRIVATE_SYNTAX_DENSITY:
            sig.get("private_syntax_density"),
        AlignmentTarget.PREDICTION_PROFILES:
            dev.get("durable_prediction_improvement_score"),
        AlignmentTarget.ACTION_EFFECT_PROFILES:
            dev.get("durable_action_effect_learning_score"),
        AlignmentTarget.HABIT_PROFILES: sig.get("habit_profile")
            or metrics.get("habit_profile"),
        AlignmentTarget.BOUNDARY_CLARITY_PROFILES:
            sig.get("boundary_clarity_score"),
        AlignmentTarget.SOURCE_DIET_PROFILES: run.get("source_diet"),
        AlignmentTarget.CONTAMINATION_PROFILES:
            sig.get("human_label_contamination_score"),
        AlignmentTarget.PLATEAU_REGRESSION_EVENTS:
            (dev.get("plateau_count"), dev.get("regression_count")),
        AlignmentTarget.SAFETY_BLOCKS:
            soak.get("soak_safety_block_count")
            or dev.get("developmental_safety_block_count"),
    }
    return table.get(target)


def _jaccard(a: Dict, b: Dict) -> float:
    ka, kb = set(a or {}), set(b or {})
    union = ka | kb
    return (len(ka & kb) / len(union)) if union else 1.0


@dataclass
class CrossRunAlignment:
    """Aligns comparable structures across two runs, preserving differences."""

    def align_target(self, run_a: Dict[str, Any], run_b: Dict[str, Any],
                     target: str) -> AlignmentResult:
        va, vb = _extract(run_a, target), _extract(run_b, target)
        if va is None or vb is None:
            return AlignmentResult(target, AlignmentStatus.INCONCLUSIVE,
                                   detail="missing data in one or both runs")
        if isinstance(va, dict) and isinstance(vb, dict):
            overlap = _jaccard(va, vb)
            status = (AlignmentStatus.ALIGNED if overlap >= 0.6
                      else AlignmentStatus.PARTIAL if overlap >= 0.3
                      else AlignmentStatus.DIVERGENT)
            diffs = sorted(set(va) ^ set(vb))
            return AlignmentResult(target, status, overlap=overlap,
                                   detail=f"family Jaccard {overlap:.2f}",
                                   run_specific_differences=diffs[:8])
        a, b = _numeric(va), _numeric(vb)
        if a is None or b is None:
            return AlignmentResult(target, AlignmentStatus.PARTIAL,
                                   detail=f"{va!r} vs {vb!r}")
        denom = max(abs(a), abs(b), 1.0)
        overlap = max(0.0, 1.0 - abs(a - b) / denom)
        status = (AlignmentStatus.ALIGNED if overlap >= 0.8
                  else AlignmentStatus.PARTIAL if overlap >= 0.4
                  else AlignmentStatus.DIVERGENT)
        return AlignmentResult(target, status, overlap=overlap,
                               detail=f"{a} vs {b}")

    def align(self, run_a: Dict[str, Any], run_b: Dict[str, Any],
              targets=None) -> Dict[str, Any]:
        targets = targets or AlignmentTarget.ALL
        results = [self.align_target(run_a, run_b, t) for t in targets]
        counts: Dict[str, int] = {s: 0 for s in AlignmentStatus.ALL}
        for r in results:
            counts[r.status] = counts.get(r.status, 0) + 1
        return {
            "run_a": run_a.get("run_id"), "run_b": run_b.get("run_id"),
            "results": [r.to_dict() for r in results],
            "aligned_count": counts[AlignmentStatus.ALIGNED],
            "partial_count": counts[AlignmentStatus.PARTIAL],
            "inconclusive_count": counts[AlignmentStatus.INCONCLUSIVE],
            "divergent_count": counts[AlignmentStatus.DIVERGENT],
            "note": "alignment preserves run-specific differences; missing "
                    "data is partial/inconclusive, never forced",
        }


def _numeric(value: Any):
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, tuple):
        nums = [v for v in value if isinstance(v, (int, float))]
        return float(sum(nums)) if nums else None
    return None
