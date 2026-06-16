"""Divergence analysis -- why did two runs develop differently?

:class:`DivergenceDetector` explains low cross-run similarity conservatively: a
different sensorium diet or seed, live flux variability, source silence or
corruption, overload/deprivation, human-label contamination, fixture overfit, an
action-policy difference, habit rigidity, boundary confusion, restart
discontinuity, or an unknown cause. Divergence is NOT failure by default;
unknown divergence stays visible rather than being explained away.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class DivergenceReason:
    DIFFERENT_SENSORIUM_DIET = "different_sensorium_diet"
    DIFFERENT_SEED = "different_seed"
    LIVE_FLUX_VARIABILITY = "live_flux_variability"
    SOURCE_SILENCE = "source_silence"
    SOURCE_CORRUPTION = "source_corruption"
    OVERLOAD_DEPRIVATION = "overload_deprivation"
    HUMAN_LABEL_CONTAMINATION = "human_label_contamination"
    FIXTURE_OVERFIT = "fixture_overfit"
    ACTION_POLICY_DIFFERENCE = "action_policy_difference"
    HABIT_RIGIDITY = "habit_rigidity"
    BOUNDARY_CONFUSION = "boundary_confusion"
    RESTART_DISCONTINUITY = "restart_discontinuity"
    UNKNOWN = "unknown"

    ALL = (DIFFERENT_SENSORIUM_DIET, DIFFERENT_SEED, LIVE_FLUX_VARIABILITY,
           SOURCE_SILENCE, SOURCE_CORRUPTION, OVERLOAD_DEPRIVATION,
           HUMAN_LABEL_CONTAMINATION, FIXTURE_OVERFIT, ACTION_POLICY_DIFFERENCE,
           HABIT_RIGIDITY, BOUNDARY_CONFUSION, RESTART_DISCONTINUITY, UNKNOWN)


@dataclass
class DevelopmentalDivergence:
    """A single explained (or explicitly unexplained) divergence."""

    run_a: str
    run_b: str
    reason: str
    confidence: str = "low"
    evidence: str = ""
    is_failure: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"run_a": self.run_a, "run_b": self.run_b, "reason": self.reason,
                "confidence": self.confidence, "evidence": self.evidence,
                "is_failure": self.is_failure}


@dataclass
class DivergenceDetector:
    """Detects and conservatively explains divergence between two runs."""

    def detect(self, run_a: Dict[str, Any], run_b: Dict[str, Any], *,
               similarity: float = 1.0,
               similarity_threshold: float = 0.6,
               ) -> List[DevelopmentalDivergence]:
        out: List[DevelopmentalDivergence] = []
        rid_a, rid_b = run_a.get("run_id"), run_b.get("run_id")
        if similarity >= similarity_threshold:
            return out  # not meaningfully divergent

        def add(reason, confidence, evidence, failure=False) -> None:
            out.append(DevelopmentalDivergence(rid_a, rid_b, reason, confidence,
                                               evidence, failure))

        if run_a.get("sensorium_profile") != run_b.get("sensorium_profile"):
            add(DivergenceReason.DIFFERENT_SENSORIUM_DIET, "moderate",
                f"{run_a.get('sensorium_profile')} vs "
                f"{run_b.get('sensorium_profile')}")
        if (run_a.get("seed") is not None and run_b.get("seed") is not None
                and run_a.get("seed") != run_b.get("seed")):
            add(DivergenceReason.DIFFERENT_SEED, "moderate",
                f"seed {run_a.get('seed')} vs {run_b.get('seed')}")
        live = {run_a.get("fixture_live_replay"),
                run_b.get("fixture_live_replay")}
        if "live" in live:
            add(DivergenceReason.LIVE_FLUX_VARIABILITY, "low",
                "at least one run used live read-only flux")

        for run, other in ((run_a, run_b), (run_b, run_a)):
            sig = run.get("world_signature", {})
            dev = run.get("developmental_profile", {})
            if _f(sig.get("human_label_contamination_score")) >= 0.5:
                add(DivergenceReason.HUMAN_LABEL_CONTAMINATION, "moderate",
                    f"{run.get('run_id')} contamination "
                    f"{sig.get('human_label_contamination_score')}", True)
            if dev.get("structural_growth_status") == "fixture_overfit":
                add(DivergenceReason.FIXTURE_OVERFIT, "moderate",
                    f"{run.get('run_id')} flagged fixture overfit", True)
            if _i(dev.get("regression_count")) > 0 and \
                    _i(other.get("developmental_profile", {}).get(
                        "regression_count")) == 0:
                add(DivergenceReason.RESTART_DISCONTINUITY, "low",
                    f"{run.get('run_id')} has regressions the other lacks")

        if not out:
            add(DivergenceReason.UNKNOWN, "low",
                f"runs diverge (similarity {similarity:.2f}) with no identified "
                "cause; preserved as visible unknown")
        return out


def _f(v) -> float:
    return float(v) if isinstance(v, (int, float)) else 0.0


def _i(v) -> int:
    return int(v) if isinstance(v, (int, float)) else 0
