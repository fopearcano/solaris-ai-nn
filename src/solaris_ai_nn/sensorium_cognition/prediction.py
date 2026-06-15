"""Prediction -- sign-grounded predictions whose successes AND failures are kept.

The :class:`PredictionEngine` produces :class:`SensoriumPrediction`s about the next
sign, missing signs, source silence, receptor pressure, cross-modal relations, and
metabolic risks. Prediction success/failure is stored; failed predictions are
useful evidence and are never hidden, and prediction is never overstated as
understanding.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class PredictionType:
    NEXT_SIGN = "next_sign"
    MISSING_SIGN = "missing_sign"
    SOURCE_SILENCE = "source_silence"
    RECEPTOR_PRESSURE = "receptor_pressure"
    BASELINE_SHIFT = "baseline_shift"
    CROSS_MODAL_RELATION = "cross_modal_relation"
    LOGOS_TENSION = "logos_tension"
    ATTENTION_NEED = "attention_need"
    OVERLOAD_RISK = "overload_risk"
    DEPRIVATION_RISK = "deprivation_risk"

    ALL = (NEXT_SIGN, MISSING_SIGN, SOURCE_SILENCE, RECEPTOR_PRESSURE,
           BASELINE_SHIFT, CROSS_MODAL_RELATION, LOGOS_TENSION, ATTENTION_NEED,
           OVERLOAD_RISK, DEPRIVATION_RISK)


class PredictionOutcome:
    UNKNOWN = "unknown"
    SUCCESS = "success"
    FAILURE = "failure"

    ALL = (UNKNOWN, SUCCESS, FAILURE)


@dataclass
class SensoriumPrediction:
    """One sign-grounded prediction (outcome tracked; failures preserved)."""

    prediction_type: str
    predicted_target: str
    prediction_id: str = field(
        default_factory=lambda: f"PRED_{uuid.uuid4().hex[:8]}")
    evidence_refs: List[str] = field(default_factory=list)
    confidence: float = 0.0
    uncertainty: float = 0.0
    time_horizon: int = 1
    modality_scope: str = ""
    source_scope: str = ""
    later_outcome: Optional[str] = None
    outcome: str = PredictionOutcome.UNKNOWN

    def resolve(self, observed_targets: List[str]) -> str:
        """Resolve against observed targets; records success OR failure."""
        if self.predicted_target in observed_targets:
            self.outcome = PredictionOutcome.SUCCESS
            self.later_outcome = self.predicted_target
        else:
            self.outcome = PredictionOutcome.FAILURE
            self.later_outcome = "not_observed"
        return self.outcome

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "prediction_type": self.prediction_type,
            "predicted_target": self.predicted_target,
            "evidence_refs": list(self.evidence_refs),
            "confidence": round(self.confidence, 4),
            "uncertainty": round(self.uncertainty, 4),
            "time_horizon": self.time_horizon,
            "modality_scope": self.modality_scope,
            "source_scope": self.source_scope,
            "later_outcome": self.later_outcome,
            "outcome": self.outcome,
            "note": "prediction over signs; outcome tracked, failures kept; not "
                    "proof of understanding",
        }


@dataclass
class PredictionResult:
    predictions: List[SensoriumPrediction] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        resolved = [p for p in self.predictions
                    if p.outcome != PredictionOutcome.UNKNOWN]
        if not resolved:
            return 0.0
        ok = sum(1 for p in resolved if p.outcome == PredictionOutcome.SUCCESS)
        return round(ok / len(resolved), 4)

    @property
    def failed(self) -> List[SensoriumPrediction]:
        return [p for p in self.predictions
                if p.outcome == PredictionOutcome.FAILURE]

    def to_dict(self) -> Dict[str, Any]:
        return {"prediction_count": len(self.predictions),
                "success_rate": self.success_rate,
                "failed_count": len(self.failed),
                "predictions": [p.to_dict() for p in self.predictions]}


@dataclass
class PredictionEngine:
    """Generates sign-grounded predictions from patterns and metabolic state."""

    def predict(self, signs: List[Any], patterns: List[Any], *,
                metabolism: Optional[Dict[str, Any]] = None,
                max_predictions: int = 50) -> PredictionResult:
        result = PredictionResult()
        by_id = {getattr(s, "sign_id", ""): s for s in signs}

        # Sequence/predicts patterns -> next-sign predictions.
        for pat in patterns:
            if len(result.predictions) >= max_predictions:
                break
            rel = getattr(pat, "relation", "")
            psigns = list(getattr(pat, "signs", []))
            if rel in ("sequence", "predicts") and len(psigns) >= 2:
                target = by_id.get(psigns[1])
                result.predictions.append(SensoriumPrediction(
                    prediction_type=PredictionType.NEXT_SIGN,
                    predicted_target=psigns[1],
                    evidence_refs=[getattr(pat, "pattern_id", "")],
                    confidence=float(getattr(pat, "strength", 0.0)),
                    uncertainty=round(1.0 - float(getattr(pat, "strength",
                                                          0.0)), 4),
                    modality_scope=(target.dominant_modality
                                    if target is not None else "")))
            elif rel in ("before_absence", "after_absence") and psigns:
                result.predictions.append(SensoriumPrediction(
                    prediction_type=PredictionType.MISSING_SIGN,
                    predicted_target=psigns[0],
                    evidence_refs=[getattr(pat, "pattern_id", "")],
                    confidence=0.4, uncertainty=0.6))

        # Metabolic risks -> overload / deprivation predictions.
        m = metabolism or {}
        if m.get("overload_state"):
            result.predictions.append(SensoriumPrediction(
                prediction_type=PredictionType.OVERLOAD_RISK,
                predicted_target="perceptual_metabolism",
                evidence_refs=["metabolism:overload"], confidence=0.6,
                uncertainty=0.4))
        if m.get("deprivation_state"):
            result.predictions.append(SensoriumPrediction(
                prediction_type=PredictionType.DEPRIVATION_RISK,
                predicted_target="perceptual_metabolism",
                evidence_refs=["metabolism:deprivation"], confidence=0.5,
                uncertainty=0.5))
        return result
