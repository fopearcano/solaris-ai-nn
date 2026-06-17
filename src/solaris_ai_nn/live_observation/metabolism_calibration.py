"""Perceptual metabolism calibration -- report-only threshold recommendations.

:class:`PerceptualMetabolismCalibrator` reads the observed live field (source health,
source diet, rhythm, absence, overload/deprivation) and proposes report-only
perceptual-metabolism thresholds: max event rate, max payload, per-source weighting,
novelty pressure, repetition tolerance, silence tolerance, quarantine/overload/
deprivation thresholds, and the weights for the operator pulse, human text, debug
gloss, scalar readings, and absence signals.

Nothing here is applied: no feeder, governance, configuration, or learning state is
written or changed. The operator decides whether and how to act on the recommendation.
Calibration is descriptive metabolism, not consciousness, life, or understanding.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MetabolismThresholdRecommendation:
    """One report-only recommended threshold/weight (never applied)."""

    name: str
    recommended_value: float
    rationale: str = ""
    unit: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name,
                "recommended_value": round(self.recommended_value, 4),
                "unit": self.unit, "rationale": self.rationale,
                "applied": False}


@dataclass
class MetabolismCalibrationResult:
    """The full report-only metabolism calibration."""

    recommendations: List[MetabolismThresholdRecommendation] = field(
        default_factory=list)
    source_weights: Dict[str, float] = field(default_factory=dict)
    confidence: str = "low"
    findings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation_count": len(self.recommendations),
            "recommendations": [r.to_dict() for r in self.recommendations],
            "source_weights": {k: round(v, 4)
                               for k, v in self.source_weights.items()},
            "calibration_confidence": self.confidence,
            "findings": list(self.findings),
            "applied": False,
            "note": "metabolism calibration is report-only; no feeder, "
                    "governance, configuration, or learning state is written or "
                    "changed; the operator decides whether to act; this is "
                    "descriptive metabolism, not consciousness or understanding",
        }


@dataclass
class PerceptualMetabolismCalibrator:
    """Proposes report-only perceptual-metabolism thresholds from observations."""

    base_max_event_rate_per_min: float = 120.0
    base_max_payload_bytes: int = 64_000

    def calibrate(self, *, source_health_summary: Dict[str, Any],
                  source_diet: Dict[str, Any], rhythm: Dict[str, Any],
                  absence: Dict[str, Any],
                  load: Dict[str, Any]) -> MetabolismCalibrationResult:
        result = MetabolismCalibrationResult()
        rec = result.recommendations.append

        load_status = load.get("load_status", "unknown")
        # Max event rate: tighten under overload, relax (slightly) when stable.
        rate = self.base_max_event_rate_per_min
        if load_status in ("severe_overload", "mild_overload"):
            rate *= 0.5
        rec(MetabolismThresholdRecommendation(
            "max_event_rate_per_min", rate, unit="events/min",
            rationale=f"load status is {load_status!r}"))
        rec(MetabolismThresholdRecommendation(
            "max_payload_bytes", float(self.base_max_payload_bytes),
            unit="bytes", rationale="bounded payload size for metabolism"))

        # Novelty pressure vs repetition tolerance from source diet dominance.
        dominance = float(source_diet.get(
            "live_source_diet_dominance_score", 0.0))
        novelty = min(1.0, 0.4 + dominance * 0.5)
        rec(MetabolismThresholdRecommendation(
            "novelty_pressure", novelty,
            rationale=f"dominance score {dominance:.2f}; favour novelty when one "
            "source dominates"))
        rec(MetabolismThresholdRecommendation(
            "repetition_tolerance", max(0.1, 1.0 - dominance),
            rationale="lower tolerance for repetition under high dominance"))

        # Silence tolerance from absence windows.
        deprivation_windows = int(absence.get("deprivation_window_count", 0))
        silence_tolerance = 0.8 if deprivation_windows == 0 else 0.5
        rec(MetabolismThresholdRecommendation(
            "silence_tolerance", silence_tolerance,
            rationale="absence is a valid signal; tolerate silence but watch "
            "deprivation"))

        # Quarantine / overload / deprivation thresholds (report-only guards).
        rec(MetabolismThresholdRecommendation(
            "quarantine_rate_threshold", 0.2,
            rationale="flag sources whose quarantine rate exceeds 20%"))
        rec(MetabolismThresholdRecommendation(
            "overload_rate_threshold", rate * 1.5, unit="events/min",
            rationale="treat sustained rate above this as overload"))
        rec(MetabolismThresholdRecommendation(
            "deprivation_silence_threshold_s", 3600.0, unit="seconds",
            rationale="global silence beyond this suggests deprivation"))

        # Per-signal weights: operator pulse is stimulus, not the ontology.
        op = float(source_diet.get("live_operator_pulse_dominance_score", 0.0))
        human = float(source_diet.get("human_text_proportion", 0.0))
        result.source_weights = {
            "operator_pulse": round(max(0.1, 0.5 - op * 0.4), 4),
            "human_text": round(max(0.1, 0.5 - human * 0.4), 4),
            "debug_gloss": 0.0,
            "scalar_reading": 0.8,
            "absence": 0.6,
        }
        for name, weight in result.source_weights.items():
            rec(MetabolismThresholdRecommendation(
                f"weight_{name}", weight,
                rationale=("debug gloss is never ground truth"
                           if name == "debug_gloss"
                           else "report-only signal weight")))

        # Confidence reflects how much real signal we saw.
        live_sources = int(source_health_summary.get("live_source_count", 0))
        rhythm_count = int(rhythm.get("rhythm_pattern_count", 0))
        if live_sources >= 3 and rhythm_count >= 2 and deprivation_windows == 0:
            result.confidence = "moderate"
        elif live_sources >= 2:
            result.confidence = "low"
        else:
            result.confidence = "very_low"
            result.findings.append(
                "too few live sources for a confident calibration")
        if load.get("blocks_ontogenesis_recommendation"):
            result.findings.append(
                "severe overload/deprivation present; calibration is provisional")
        return result
