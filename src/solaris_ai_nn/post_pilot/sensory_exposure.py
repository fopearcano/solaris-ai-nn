"""Post-pilot sensory-exposure comparison (Prompt 32).

Compares Pilot-1 nursery-only artifacts against Pilot-2 read-only sensory (and
mixed) artifacts and classifies whether read-only environmental exposure
improved grounding, added noise only, caused overload, or was inconclusive.
Cautious by construction: a missing comparable arm yields ``inconclusive``,
and no causal or cognitive claim is made.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class SensoryExposureClassification:
    IMPROVED_GROUNDING = "sensory_exposure_improved_grounding"
    ADDED_NOISE_ONLY = "sensory_exposure_added_noise_only"
    CAUSED_OVERLOAD = "sensory_exposure_caused_overload"
    INCONCLUSIVE = "sensory_exposure_inconclusive"

    ALL = (IMPROVED_GROUNDING, ADDED_NOISE_ONLY, CAUSED_OVERLOAD,
           INCONCLUSIVE)


@dataclass
class SensoryExposureComparison:
    """Cautious comparison of nursery-only vs sensory/mixed exposure."""

    classification: str = SensoryExposureClassification.INCONCLUSIVE
    observed_differences: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    disclaimer: str = ("Differences are observed associations from bounded "
                       "runs, not proven causal effects; read-only exposure "
                       "is not evidence of consciousness or understanding.")

    def to_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


def classify_sensory_exposure(
        nursery_only: Optional[Dict[str, Any]],
        sensory: Optional[Dict[str, Any]]) -> SensoryExposureComparison:
    """Classify the effect of read-only sensory exposure vs a nursery baseline.

    Each arg is a small metrics dict (e.g. symbol_stability, ambiguity_ratio,
    prediction_score, malformed_event_rate, overload_signal,
    grounding_quality, provenance_completeness). Missing data -> inconclusive.
    """
    result = SensoryExposureComparison()
    if not nursery_only or not sensory:
        result.reasons.append("missing comparable arm; inconclusive")
        return result

    def g(d: Dict[str, Any], key: str, default: float = 0.0) -> float:
        try:
            return float(d.get(key, default) or default)
        except (TypeError, ValueError):
            return default

    diffs = result.observed_differences
    overload = bool(sensory.get("overload_signal")) or \
        g(sensory, "malformed_event_rate") > 0.5 or \
        int(sensory.get("sensory_noise_overload_count", 0) or 0) > 0
    grounding_ok = str(sensory.get("grounding_quality", "")) in (
        "moderate", "strong") or sensory.get("has_grounding_evidence")
    prediction_delta = g(sensory, "prediction_score") - \
        g(nursery_only, "prediction_score")
    stability_delta = g(sensory, "symbol_stability") - \
        g(nursery_only, "symbol_stability")
    ambiguity_delta = g(sensory, "ambiguity_ratio") - \
        g(nursery_only, "ambiguity_ratio")

    if prediction_delta != 0:
        diffs.append(f"prediction delta {round(prediction_delta, 4)}")
    if stability_delta != 0:
        diffs.append(f"symbol-stability delta {round(stability_delta, 4)}")
    if ambiguity_delta != 0:
        diffs.append(f"ambiguity delta {round(ambiguity_delta, 4)}")

    improved = (grounding_ok and not overload
                and (prediction_delta > 0 or stability_delta > 0
                     or ambiguity_delta < 0))
    noise_only = (not improved and not overload
                  and (prediction_delta <= 0 and stability_delta <= 0))

    if overload:
        result.classification = SensoryExposureClassification.CAUSED_OVERLOAD
        result.reasons.append("sensory exposure produced overload/noise flood")
    elif improved:
        result.classification = \
            SensoryExposureClassification.IMPROVED_GROUNDING
        result.reasons.append("grounding adequate and a candidate improvement "
                              "in prediction/stability/ambiguity")
    elif noise_only:
        result.classification = SensoryExposureClassification.ADDED_NOISE_ONLY
        result.reasons.append("no candidate improvement over the nursery "
                              "baseline")
    else:
        result.reasons.append("evidence does not clearly separate "
                              "improvement from noise")
    return result
